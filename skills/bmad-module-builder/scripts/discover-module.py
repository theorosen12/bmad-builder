#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Read-only inventory + data-quality scan of a BMAD module repo.

Emits a single JSON document describing what a module contains and what an
author should look at before migrating to the plugin.json format. Writes
NOTHING. Consumed by the bmad-module-migrator skill (and usable standalone for
the builder's Validate Module path).

Reports:
  - manifests:  plugin.json / marketplace.json presence + summary
  - package.json metadata
  - module.yaml (code/name/description/default_selected/agent roster)
  - module-help.csv (header, row count, canonical-header match, skill column)
  - skills[]:   SKILL.md dirs with frontmatter name, customize.toml kind
  - customize_schemas[], claude_subagents[]
  - required files (README/LICENSE/CHANGELOG) + LICENSE SPDX sniff
  - .bmadignore presence
  - identity: current code, reserved?, de-"bmad-" name candidate, suggested code
  - data_quality[]: reserved code, empty description, bmad- prefixes, CSV header
    mismatch, _meta row, orphan CSV rows, skills missing capability rows
"""

import argparse
import csv
import json
import os
import re
import sys
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spec_constants import RESERVED_CODES, NAME_REGEX, CODE_REGEX  # noqa: E402

SKILL_WALK_DENYLIST = {
    ".git",
    "node_modules",
    ".github",
    ".husky",
    ".trunk",
    "__pycache__",
    ".claude-plugin",
    "website",
}

# Current canonical CSV header for BMB modules (preceded-by/followed-by columns).
CANONICAL_CSV_HEADER = [
    "module", "skill", "display-name", "menu-code", "description",
    "action", "args", "phase", "preceded-by", "followed-by", "required",
    "output-location", "outputs",
]

_SPDX_SNIFF = {
    "MIT": re.compile(r"MIT License", re.I),
    "Apache-2.0": re.compile(r"Apache License", re.I),
    "BSD-2-Clause": re.compile(r"BSD 2-Clause", re.I),
    "BSD-3-Clause": re.compile(r"BSD 3-Clause", re.I),
    "ISC": re.compile(r"ISC License", re.I),
    "GPL-3.0": re.compile(r"GNU GENERAL PUBLIC LICENSE", re.I),
    "AGPL-3.0": re.compile(r"AFFERO GENERAL PUBLIC LICENSE", re.I),
}


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _strip_scalar(value: str) -> str:
    value = value.strip()
    idx = value.find(" #")
    if value and value[0] not in "\"'" and idx != -1:
        value = value[:idx].rstrip()
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        return value[1:-1]
    return value


def parse_frontmatter_name(skill_md: Path) -> str | None:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.match(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n", text)
    if not m:
        return None
    for line in m.group(1).splitlines():
        if line.startswith("name:"):
            return _strip_scalar(line.partition(":")[2])
    return None


def parse_module_yaml(path: Path) -> dict:
    """Top-level scalars plus the `agents:` roster codes."""
    out: dict = {"_agents": []}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    in_agents = False
    for line in text.splitlines():
        if re.match(r"^agents:\s*$", line):
            in_agents = True
            continue
        if in_agents:
            mcode = re.match(r"^\s+-\s+code:\s*(.+)$", line)
            if mcode:
                out["_agents"].append(_strip_scalar(mcode.group(1)))
                continue
            if line and not line[0].isspace():
                in_agents = False
        if line and line[0] not in " \t#-" and ":" in line:
            key, _, raw = line.partition(":")
            out[key.strip()] = _strip_scalar(raw)
    return out


def customize_kind(toml_path: Path) -> str:
    try:
        text = toml_path.read_text(encoding="utf-8")
    except OSError:
        return "none"
    for line in text.splitlines():
        s = line.strip()
        if s == "[agent]" or s.startswith("[agent."):
            return "agent"
        if s == "[workflow]" or s.startswith("[workflow."):
            return "workflow"
    return "unknown"


def discover_skills(root: Path):
    skills = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKILL_WALK_DENYLIST]
        if "SKILL.md" in filenames:
            d = Path(dirpath)
            rel = "./" + os.path.relpath(dirpath, root).replace(os.sep, "/")
            basename = d.name
            fm_name = parse_frontmatter_name(d / "SKILL.md")
            has_customize = (d / "customize.toml").is_file()
            kind = customize_kind(d / "customize.toml") if has_customize else "none"
            is_agent = kind == "agent" or bool(re.search(r"(^|-)agent-", basename))
            skills.append(
                {
                    "path": rel,
                    "basename": basename,
                    "frontmatter_name": fm_name,
                    "name_matches_basename": fm_name == basename,
                    "has_customize": has_customize,
                    "customize_kind": kind,
                    "is_persona_agent": is_agent,
                }
            )
    skills.sort(key=lambda s: s["path"])
    return skills


def find_first(root: Path, candidates):
    for c in candidates:
        if (root / c).is_file():
            return c
    return None


def sniff_spdx(root: Path):
    lic = root / "LICENSE"
    if not lic.is_file():
        return None
    try:
        head = " ".join(lic.read_text(encoding="utf-8").split("\n")[:3])
    except OSError:
        return None
    for spdx, pat in _SPDX_SNIFF.items():
        if pat.search(head):
            return spdx
    return None


def discover(root: Path, module_def_arg=None, module_csv_arg=None) -> dict:
    dq = []

    def add_dq(code, severity, message):
        dq.append({"code": code, "severity": severity, "message": message})

    # --- manifests ---
    plugin_path = root / ".claude-plugin" / "plugin.json"
    mkt_path = root / ".claude-plugin" / "marketplace.json"
    marketplace = read_json(mkt_path) if mkt_path.is_file() else None
    mkt_summary = None
    if marketplace:
        plugins = marketplace.get("plugins") if isinstance(marketplace.get("plugins"), list) else []
        mkt_summary = {
            "name": marketplace.get("name"),
            "plugin_count": len(plugins),
            "plugins": [
                {
                    "name": p.get("name"),
                    "version": p.get("version"),
                    "description": p.get("description"),
                    "skills": p.get("skills", []),
                }
                for p in plugins
            ],
        }

    # --- package.json ---
    package = read_json(root / "package.json") if (root / "package.json").is_file() else None
    pkg_summary = None
    if package:
        pkg_summary = {k: package.get(k) for k in (
            "name", "version", "description", "author", "license", "repository", "homepage", "keywords"
        )}

    # --- module.yaml ---
    mod_def_rel = module_def_arg or find_first(root, ["skills/module.yaml", "src/module.yaml", "module.yaml"])
    module_yaml = parse_module_yaml(root / mod_def_rel) if mod_def_rel else {}
    mod_def_summary = None
    if mod_def_rel:
        mod_def_summary = {
            "path": mod_def_rel,
            "code": module_yaml.get("code"),
            "name": module_yaml.get("name"),
            "description": module_yaml.get("description"),
            "default_selected": module_yaml.get("default_selected"),
            "agent_roster": module_yaml.get("_agents", []),
        }

    # --- module-help.csv ---
    csv_rel = module_csv_arg or find_first(root, ["skills/module-help.csv", "src/module-help.csv", "module-help.csv"])
    csv_summary = None
    csv_skills = []
    if csv_rel:
        try:
            text = (root / csv_rel).read_text(encoding="utf-8")
            reader = csv.DictReader(StringIO(text))
            header = reader.fieldnames or []
            rows = list(reader)
            csv_skills = [r.get("skill", "").strip() for r in rows if r.get("skill", "").strip()]
            csv_summary = {
                "path": csv_rel,
                "header": header,
                "rows": len(rows),
                "header_matches_canonical": header == CANONICAL_CSV_HEADER,
                "skills_in_csv": csv_skills,
            }
        except Exception as e:  # noqa: BLE001
            csv_summary = {"path": csv_rel, "error": str(e)}

    # --- skills ---
    skills = discover_skills(root)
    skill_basenames = [s["basename"] for s in skills]
    customize_schemas = sorted(
        s["path"].rstrip("/") + "/customize.toml" for s in skills if s["has_customize"]
    )

    # --- claude subagents ---
    agents_dir = root / "agents"
    claude_subagents = []
    if agents_dir.is_dir():
        claude_subagents = sorted(
            "./agents/" + p.name for p in agents_dir.iterdir() if p.is_file() and p.suffix == ".md"
        )

    # --- required files ---
    required = {
        "readme": (root / "README.md").is_file(),
        "license": (root / "LICENSE").is_file(),
        "changelog": (root / "CHANGELOG.md").is_file(),
        "license_spdx_sniff": sniff_spdx(root),
    }

    bmadignore_present = (root / ".bmadignore").is_file()

    # --- identity ---
    current_code = module_yaml.get("code")
    mkt_name = (mkt_summary["plugins"][0]["name"] if mkt_summary and mkt_summary["plugins"] else None) or (
        mkt_summary["name"] if mkt_summary else None
    )
    name_candidate = re.sub(r"^bmad-", "", mkt_name) if mkt_name else None
    code_reserved = bool(current_code and current_code in RESERVED_CODES)
    suggested_code = None
    if name_candidate and CODE_REGEX.match(name_candidate) and name_candidate not in RESERVED_CODES and len(name_candidate) <= 31:
        suggested_code = name_candidate
    identity = {
        "current_code": current_code,
        "code_reserved": code_reserved,
        "name_candidate": name_candidate,
        "name_warns_bmad_prefix": bool(mkt_name and mkt_name.startswith("bmad-")),
        "suggested_code": suggested_code,
    }

    # --- data quality ---
    if code_reserved:
        add_dq("reserved-code", "high",
                f'module.yaml code "{current_code}" is reserved (spec §7.1); remap bmad.code and update module.yaml (C10)')
    if mod_def_summary is not None and not (mod_def_summary.get("description") or "").strip():
        add_dq("empty-description", "medium",
                "module.yaml description is empty; synthesize a 10-200 char description for plugin.json")
    if mkt_name and mkt_name.startswith("bmad-"):
        add_dq("bmad-name-prefix", "low",
                f'marketplace name "{mkt_name}" uses the reserved "bmad-" prefix (W02); drop it unless a verified org')
    bmad_skills = [b for b in skill_basenames if b.startswith("bmad-")]
    if bmad_skills:
        add_dq("bmad-skill-names", "info",
                f"{len(bmad_skills)} skill name(s) use the 'bmad-' prefix (W02/W03); renaming is high blast-radius — defer as future cleanup")
    for s in skills:
        if not s["name_matches_basename"]:
            add_dq("frontmatter-name-mismatch", "high",
                    f'{s["path"]}/SKILL.md frontmatter name "{s["frontmatter_name"]}" != dir basename "{s["basename"]}" (C09)')
    if csv_summary and "error" not in csv_summary:
        if not csv_summary["header_matches_canonical"]:
            add_dq("csv-header-mismatch", "medium",
                    f"module-help.csv header differs from canonical {CANONICAL_CSV_HEADER}")
        if "_meta" in csv_skills:
            add_dq("csv-meta-row", "info", "module-help.csv contains a _meta row (informational; not a skill)")
        fs_set = set(skill_basenames)
        setup_names = {s["basename"] for s in skills if s["basename"].endswith("-setup")}
        for cs in csv_skills:
            if cs == "_meta" or cs in setup_names:
                continue
            if cs not in fs_set:
                add_dq("orphan-csv-row", "high",
                        f'module-help.csv references skill "{cs}" which has no directory on disk')
        csv_set = set(csv_skills)
        for s in skills:
            if s["basename"] in csv_set or s["basename"].endswith("-setup"):
                continue
            if s["is_persona_agent"]:
                add_dq("agent-no-capability-row", "info",
                        f'persona-agent skill "{s["basename"]}" has no capability row (expected; routed via module.yaml agents roster)')
            else:
                add_dq("missing-csv-row", "high",
                        f'skill "{s["basename"]}" has no capability row in module-help.csv')

    return {
        "module_root": str(root),
        "manifests": {
            "plugin_json": {"present": plugin_path.is_file(), "path": str(plugin_path) if plugin_path.is_file() else None},
            "marketplace_json": {"present": mkt_path.is_file(), "path": str(mkt_path) if mkt_path.is_file() else None, "summary": mkt_summary},
        },
        "package_json": pkg_summary,
        "module_definition": mod_def_summary,
        "module_help_csv": csv_summary,
        "skills": skills,
        "customize_schemas": customize_schemas,
        "claude_subagents": claude_subagents,
        "required_files": required,
        "bmadignore_present": bmadignore_present,
        "identity": identity,
        "counts": {
            "skills": len(skills),
            "customize_schemas": len(customize_schemas),
            "agent_skills": sum(1 for s in skills if s["is_persona_agent"]),
            "claude_subagents": len(claude_subagents),
            "data_quality_issues": len(dq),
        },
        "data_quality": dq,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only inventory + data-quality scan of a BMAD module")
    p.add_argument("--module-root", default=".", help="Path to the module root (default: cwd)")
    p.add_argument("--module-definition", help="explicit relative path to module.yaml")
    p.add_argument("--module-help-csv", help="explicit relative path to module-help.csv")
    args = p.parse_args()

    root = Path(args.module_root).resolve()
    if not root.is_dir():
        print(json.dumps({"status": "error", "message": f"Not a directory: {root}"}))
        return 2

    print(json.dumps(discover(root, args.module_definition, args.module_help_csv), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
