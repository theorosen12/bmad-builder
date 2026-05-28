#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Synthesize a spec-conformant .claude-plugin/plugin.json for a BMAD module.

Shared by the Create Module (CM) path of bmad-module-builder and by the
bmad-module-migrator skill. Deterministic and non-interactive: it reads
module.yaml + package.json + marketplace.json + the filesystem, applies the
documented fallback chains, and writes (or, with --dry-run, only previews) the
manifest. The marketplace's validate-module.mjs remains the authoritative gate;
run validate-plugin-json.py / validate-module.mjs after writing.

Field mapping (old source -> plugin.json), each with a fallback chain:
  name        <- --name / marketplace name (de-"bmad-") / kebab(module.yaml name)
  version     <- --version / package.json / marketplace plugin / module.yaml / 0.1.0
  description <- --description / marketplace plugin / package.json / module.yaml  (10-200)
  displayName <- --display-name / module.yaml `name`
  author/repository/license/homepage/keywords <- marketplace -> package.json
  skills[]    <- filesystem SKILL.md dirs (./-prefixed, sorted; reconciled vs marketplace)
  agents[]    <- agents/*.md (Claude subagents) only
  bmad.code/compatibility <- args
  bmad.moduleDefinition/moduleHelpCsv <- args (or discovered)
  bmad.customize.schemas[] <- every customize.toml beside a discovered SKILL.md
  bmad.install.ignore[] <- --ignore / discovery-driven default (excl. when .bmadignore present)

Reserved/invalid bmad.code -> error (or structured `needs_resolution` with
--on-reserved prompt). A "bmad-" name prefix is a warning, not a block.
"""

import argparse
import json
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spec_constants import (  # noqa: E402
    SPEC_VERSION,
    RESERVED_CODES,
    NAME_REGEX,
    CODE_REGEX,
    NAME_MIN_LEN,
    NAME_MAX_LEN,
    DESCRIPTION_MIN_LEN,
    DESCRIPTION_MAX_LEN,
)

# Dirs never walked when discovering skills.
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

# Discovery-driven default for bmad.install.ignore. Each pattern is emitted only
# if its target is present (kind "always" is unconditional). Ordering mirrors the
# common dev-cruft layout of a BMB-built / published module repo.
CANDIDATE_IGNORE = [
    ("docs/**", "dir", "docs"),
    ("tests/**", "dir", "tests"),
    ("tools/**", "dir", "tools"),
    ("website/**", "dir", "website"),
    ("package.json", "file", "package.json"),
    ("package-lock.json", "file", "package-lock.json"),
    ("node_modules/**", "always", "node_modules"),
    (".husky/**", "dir", ".husky"),
    ("eslint.config.mjs", "file", "eslint.config.mjs"),
    ("prettier.config.mjs", "file", "prettier.config.mjs"),
    ("CONTRIBUTING.md", "file", "CONTRIBUTING.md"),
    ("CONTRIBUTORS.md", "file", "CONTRIBUTORS.md"),
    ("CNAME", "file", "CNAME"),
    (".npmignore", "file", ".npmignore"),
    (".npmrc", "file", ".npmrc"),
    (".markdownlint-cli2.yaml", "file", ".markdownlint-cli2.yaml"),
]


# ---------------------------------------------------------------------------
# Minimal source readers


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _strip_inline_comment(value: str) -> str:
    """Strip a trailing ` # ...` comment from an unquoted scalar."""
    idx = value.find(" #")
    return value[:idx].rstrip() if idx != -1 else value


def parse_module_yaml(path: Path) -> dict:
    """Top-level scalar keys from a module.yaml (no nesting). Handles quotes and
    inline comments on unquoted values."""
    out: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        if not line or line[0] in " \t#-":
            continue
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        raw = raw.strip()
        if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
            value = raw[1:-1]
        else:
            value = _strip_inline_comment(raw)
            if value.startswith(">") or value.startswith("|"):
                value = ""
        out[key] = value
    return out


def kebab(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return re.sub(r"-+", "-", s)


# ---------------------------------------------------------------------------
# Discovery


def discover_skills(root: Path) -> list[str]:
    """Relative ('./'-prefixed) paths of directories containing SKILL.md, sorted."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKILL_WALK_DENYLIST]
        if "SKILL.md" in filenames:
            rel = os.path.relpath(dirpath, root)
            found.append("./" + rel.replace(os.sep, "/"))
    return sorted(found)


def discover_customize_schemas(root: Path, skill_rels: list[str]) -> list[str]:
    schemas = []
    for rel in skill_rels:
        toml = root / rel.lstrip("./") / "customize.toml"
        if toml.is_file():
            schemas.append(rel.rstrip("/") + "/customize.toml")
    return sorted(schemas)


def discover_claude_subagents(root: Path) -> list[str]:
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        return []
    return sorted(
        "./agents/" + p.name for p in agents_dir.iterdir() if p.is_file() and p.suffix == ".md"
    )


def compute_default_ignore(root: Path) -> list[str]:
    out = []
    for pattern, kind, target in CANDIDATE_IGNORE:
        t = root / target
        if kind == "always" or (kind == "dir" and t.is_dir()) or (kind == "file" and t.is_file()):
            out.append(pattern)
    return out


# ---------------------------------------------------------------------------
# Synthesis


def synthesize(args) -> dict:
    root = Path(args.module_root).resolve()
    warnings: list[str] = []
    errors: list[str] = []
    sources: dict[str, str] = {}

    # --- load sources ---
    marketplace = read_json(root / ".claude-plugin" / "marketplace.json") or {}
    package = read_json(root / "package.json") or {}
    mkt_plugin = {}
    if isinstance(marketplace.get("plugins"), list) and marketplace["plugins"]:
        mkt_plugin = marketplace["plugins"][0] or {}

    mod_def_rel = args.module_definition
    module_yaml = {}
    if mod_def_rel:
        module_yaml = parse_module_yaml(root / mod_def_rel)
    else:
        for cand in ("skills/module.yaml", "src/module.yaml", "module.yaml"):
            if (root / cand).is_file():
                module_yaml = parse_module_yaml(root / cand)
                break

    def first(*pairs):
        """Return (value, source_label) for the first non-empty value."""
        for value, label in pairs:
            if value not in (None, "", [], {}):
                return value, label
        return None, None

    # --- name ---
    if args.name:
        name = args.name
        sources["name"] = "arg"
    else:
        candidate = mkt_plugin.get("name") or marketplace.get("name")
        if candidate:
            name = re.sub(r"^bmad-", "", candidate)
            sources["name"] = "marketplace (de-bmad-)"
        else:
            name = kebab(module_yaml.get("name", ""))
            sources["name"] = "kebab(module.yaml name)"
    if not (isinstance(name, str) and NAME_REGEX.match(name) and NAME_MIN_LEN <= len(name) <= NAME_MAX_LEN):
        errors.append(f'name "{name}" must match /^[a-z][a-z0-9-]+$/ and be 3-64 chars')
    elif name.startswith("bmad-"):
        warnings.append(f'name "{name}" uses reserved "bmad-" prefix (W02); only for verified orgs')

    # --- version ---
    pkg_ver = package.get("version")
    mkt_ver = mkt_plugin.get("version")
    if pkg_ver and mkt_ver and pkg_ver != mkt_ver:
        warnings.append(f"version differs: package.json {pkg_ver} vs marketplace {mkt_ver} (using {args.version or pkg_ver})")
    version, sources["version"] = first(
        (args.version, "arg"),
        (pkg_ver, "package.json"),
        (mkt_ver, "marketplace plugin"),
        (module_yaml.get("module_version"), "module.yaml"),
        ("0.1.0", "default"),
    )

    # --- description ---
    description, sources["description"] = first(
        (args.description, "arg"),
        (mkt_plugin.get("description"), "marketplace plugin"),
        (package.get("description"), "package.json"),
        (module_yaml.get("description"), "module.yaml"),
    )
    if not description:
        errors.append("description could not be derived from any source; pass --description")
    elif not (DESCRIPTION_MIN_LEN <= len(description) <= DESCRIPTION_MAX_LEN):
        errors.append(
            f"description is {len(description)} chars; spec requires {DESCRIPTION_MIN_LEN}-{DESCRIPTION_MAX_LEN} (pass --description)"
        )

    # --- displayName ---
    display_name, sources["displayName"] = first(
        (args.display_name, "arg"),
        (module_yaml.get("name"), "module.yaml name"),
    )

    # --- author ---
    author = None
    if args.author_name:
        author = {"name": args.author_name}
        sources["author"] = "arg"
    elif isinstance(marketplace.get("owner"), dict) and marketplace["owner"].get("name"):
        author = {k: v for k, v in marketplace["owner"].items() if k in ("name", "email", "url") and v}
        sources["author"] = "marketplace owner"
    elif isinstance(mkt_plugin.get("author"), dict) and mkt_plugin["author"].get("name"):
        author = {k: v for k, v in mkt_plugin["author"].items() if k in ("name", "email", "url") and v}
        sources["author"] = "marketplace plugin author"
    elif package.get("author"):
        pa = package["author"]
        author = {"name": pa} if isinstance(pa, str) else {k: v for k, v in pa.items() if k in ("name", "email", "url") and v}
        sources["author"] = "package.json"

    # --- repository ---
    repository, sources["repository"] = first(
        (args.repository, "arg"),
        (marketplace.get("repository") if isinstance(marketplace.get("repository"), str) else None, "marketplace"),
        (_repo_url(package.get("repository")), "package.json"),
    )

    # --- license / homepage / keywords ---
    license_, sources["license"] = first(
        (args.license, "arg"),
        (marketplace.get("license"), "marketplace"),
        (package.get("license"), "package.json"),
    )
    homepage, sources["homepage"] = first(
        (args.homepage, "arg"),
        (marketplace.get("homepage") if isinstance(marketplace.get("homepage"), str) else None, "marketplace"),
        (package.get("homepage"), "package.json"),
    )
    keywords, sources["keywords"] = first(
        (list(args.keyword) if args.keyword else None, "arg"),
        (marketplace.get("keywords"), "marketplace"),
        (package.get("keywords"), "package.json"),
    )

    # --- skills[] (filesystem truth, reconciled vs marketplace) ---
    skills = discover_skills(root)
    sources["skills"] = "filesystem"
    mkt_skills = mkt_plugin.get("skills") if isinstance(mkt_plugin.get("skills"), list) else None
    if mkt_skills is not None:
        norm = lambda xs: {x.lstrip("./").rstrip("/") for x in xs}
        added = norm(skills) - norm(mkt_skills)
        removed = norm(mkt_skills) - norm(skills)
        if added or removed:
            warnings.append(
                "skills[] reconciled vs marketplace — "
                + (f"on disk only: {sorted(added)} " if added else "")
                + (f"marketplace only: {sorted(removed)}" if removed else "")
            )
    if not skills:
        errors.append("no skills discovered (no directory contains a SKILL.md)")

    # --- agents[] (Claude subagents only) ---
    agents = discover_claude_subagents(root)

    # --- customize schemas ---
    schemas = discover_customize_schemas(root, skills)

    # --- bmad.code ---
    code = args.code
    code_invalid = not CODE_REGEX.match(code)
    code_reserved = code in RESERVED_CODES
    if code_invalid or code_reserved:
        reason = "invalid-format" if code_invalid else "reserved"
        if args.on_reserved == "prompt":
            return {
                "status": "needs_resolution",
                "field": "bmad.code",
                "value": code,
                "reason": reason,
                "message": (
                    f'bmad.code "{code}" must match /^[a-z][a-z0-9-]{{1,31}}$/'
                    if code_invalid
                    else f'bmad.code "{code}" is reserved (spec §7.1)'
                ),
                "suggestion": kebab(name) if name and len(name) <= 31 else f"{code}x",
            }
        errors.append(
            f'bmad.code "{code}" is reserved (spec §7.1)'
            if code_reserved
            else f'bmad.code "{code}" must match /^[a-z][a-z0-9-]{{1,31}}$/'
        )

    # --- default_selected ---
    default_selected = None
    if args.default_selected is not None:
        default_selected = args.default_selected
    elif "default_selected" in module_yaml:
        default_selected = str(module_yaml["default_selected"]).strip().lower() in ("true", "yes", "1")

    # --- install.ignore (mutually exclusive with .bmadignore) ---
    bmadignore_present = (root / ".bmadignore").is_file()
    if args.no_ignore:
        ignore = None
    elif args.ignore:
        ignore = list(args.ignore)
    elif bmadignore_present:
        ignore = None
        warnings.append(".bmadignore present — omitting bmad.install.ignore (C15 exclusivity)")
    else:
        ignore = compute_default_ignore(root)
    if ignore is not None and bmadignore_present:
        errors.append("both .bmadignore and bmad.install.ignore would be present (C15)")

    # --- dependencies ---
    dep_modules = []
    for spec in args.depends_module or []:
        dep_code, _, dep_range = spec.partition(":")
        dep_modules.append({"code": dep_code.strip(), "version": (dep_range.strip() or "*")})

    # --- docs ---
    docs = OrderedDict()
    if (root / "README.md").is_file():
        docs["readme"] = "./README.md"
    if (root / "CHANGELOG.md").is_file():
        docs["changelog"] = "./CHANGELOG.md"

    # --- assemble (canonical key order; omit empty) ---
    manifest = OrderedDict()
    manifest["name"] = name
    manifest["version"] = version
    if display_name:
        manifest["displayName"] = display_name
    manifest["description"] = description
    if author:
        manifest["author"] = author
    if repository:
        manifest["repository"] = repository
    if license_:
        manifest["license"] = license_
    if homepage:
        manifest["homepage"] = homepage
    if keywords:
        manifest["keywords"] = keywords
    if skills:
        manifest["skills"] = skills
    if agents:
        manifest["agents"] = agents

    bmad = OrderedDict()
    bmad["specVersion"] = SPEC_VERSION
    bmad["code"] = code
    if display_name:
        bmad["displayName"] = display_name
    if args.category:
        bmad["category"] = args.category
    if args.subcategory:
        bmad["subcategory"] = args.subcategory
    if default_selected is not None:
        bmad["defaultSelected"] = default_selected
    compatibility = OrderedDict()
    compatibility["bmadMethod"] = args.bmad_method_range
    if args.claude_code_range:
        compatibility["claudeCode"] = args.claude_code_range
    bmad["compatibility"] = compatibility
    if args.setup_skill:
        bmad["setupSkill"] = args.setup_skill
    if mod_def_rel:
        bmad["moduleDefinition"] = mod_def_rel
    if args.module_help_csv:
        bmad["moduleHelpCsv"] = args.module_help_csv
    if schemas:
        bmad["customize"] = {"schemas": schemas}
    if dep_modules:
        bmad["dependencies"] = {"modules": dep_modules}
    install = OrderedDict()
    if ignore is not None:
        install["ignore"] = ignore
    if args.post_install_skill:
        install["postInstallSkill"] = args.post_install_skill
    if install:
        bmad["install"] = install
    if docs:
        bmad["docs"] = docs
    manifest["bmad"] = bmad

    status = "error" if errors else "success"
    return {
        "status": status,
        "manifest": manifest,
        "warnings": warnings,
        "errors": errors,
        "field_sources": sources,
        "root": str(root),
    }


def _repo_url(repo):
    if isinstance(repo, str):
        return repo
    if isinstance(repo, dict):
        return repo.get("url")
    return None


# ---------------------------------------------------------------------------
# CLI


def main() -> int:
    p = argparse.ArgumentParser(description="Synthesize a spec-conformant plugin.json")
    p.add_argument("module_root", help="Path to the module root")
    p.add_argument("--name", help="Override global module name (kebab-case)")
    p.add_argument("--code", required=True, help="bmad.code (install dir under _bmad/)")
    p.add_argument("--bmad-method-range", default=">=6.6.0", help="bmad.compatibility.bmadMethod range")
    p.add_argument("--claude-code-range", help="bmad.compatibility.claudeCode (advisory)")
    p.add_argument("--version", help="Override version (semver)")
    p.add_argument("--description", help="Override description (10-200 chars)")
    p.add_argument("--display-name", help="Override displayName")
    p.add_argument("--category", help="bmad.category")
    p.add_argument("--subcategory", help="bmad.subcategory")
    p.add_argument("--author-name", help="author.name")
    p.add_argument("--repository", help="repository URL")
    p.add_argument("--license", help="SPDX license id")
    p.add_argument("--homepage", help="homepage URL")
    p.add_argument("--keyword", action="append", help="keyword (repeatable)")
    p.add_argument("--module-definition", help="relative path to module.yaml")
    p.add_argument("--module-help-csv", help="relative path to module-help.csv")
    p.add_argument("--setup-skill", help="bmad.setupSkill name (must end in -setup)")
    p.add_argument("--post-install-skill", help="bmad.install.postInstallSkill")
    p.add_argument("--depends-module", action="append", help='module dependency "code:range" (repeatable)')
    p.add_argument("--ignore", action="append", help="bmad.install.ignore pattern (repeatable; overrides default)")
    p.add_argument("--no-ignore", action="store_true", help="omit bmad.install.ignore entirely")
    p.add_argument(
        "--default-selected",
        dest="default_selected",
        action="store_true",
        default=None,
        help="force bmad.defaultSelected true",
    )
    p.add_argument("--on-reserved", choices=["error", "prompt"], default="error",
                   help="reserved/invalid code -> hard error (default) or structured needs_resolution")
    p.add_argument("--dry-run", action="store_true", help="print manifest without writing")
    p.add_argument("--output", help="output path (default <root>/.claude-plugin/plugin.json)")
    p.add_argument("--indent", type=int, default=2, help="JSON indent (default 2)")
    args = p.parse_args()

    root = Path(args.module_root)
    if not root.is_dir():
        print(json.dumps({"status": "error", "errors": [f"Not a directory: {root}"]}, indent=2))
        return 2

    result = synthesize(args)

    if result["status"] == "needs_resolution":
        print(json.dumps(result, indent=2))
        return 3
    if result["status"] == "error":
        result["written"] = False
        result["path"] = None
        print(json.dumps(result, indent=2))
        return 2

    out_path = Path(args.output) if args.output else root.resolve() / ".claude-plugin" / "plugin.json"
    if args.dry_run:
        result["written"] = False
        result["path"] = str(out_path)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result["manifest"], indent=args.indent) + "\n", encoding="utf-8")
        result["written"] = True
        result["path"] = str(out_path)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
