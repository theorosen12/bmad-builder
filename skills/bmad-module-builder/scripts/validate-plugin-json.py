#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Validate a BMAD module's .claude-plugin/plugin.json against spec §13.

A no-Node mirror of bmad-marketplace/scripts/validate-module.mjs. Implements the
same fifteen checks (C01-C15) and four warnings (W01-W04), in the same order,
emitting the same result IDs and kinds so a `--json` run can be diffed against
the Node tool result-by-result.

  python3 validate-plugin-json.py <module-root>
  python3 validate-plugin-json.py <module-root> --json

Exit 0 on clean (warnings still printed), 1 on any error, 2 on usage error.

The marketplace's validate-module.mjs remains the AUTHORITATIVE final gate. This
port uses a hand-rolled semver and stdlib tomllib (requires-python >=3.11; C14
degrades to a warning on older runtimes). On any divergence, trust Node.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spec_constants import (  # noqa: E402
    SPEC_VERSION,
    LATEST_KNOWN_BMAD,
    RESERVED_CODES,
    KNOWN_HOOK_EVENTS,
    KNOWN_OFFICIAL_SKILLS,
    NAME_REGEX,
    CODE_REGEX,
    NAME_MIN_LEN,
    NAME_MAX_LEN,
)

# tomllib is stdlib on 3.11+. On older runtimes C14 degrades to a warning.
try:
    import tomllib  # type: ignore

    _HAVE_TOML = True
except ModuleNotFoundError:  # pragma: no cover - exercised only on <3.11
    _HAVE_TOML = False


# ---------------------------------------------------------------------------
# Minimal semver (mirrors the subset of node-semver the spec relies on).

_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def parse_version(v):
    """Return (major, minor, patch, [prerelease ids]) or None."""
    if not isinstance(v, str):
        return None
    m = _SEMVER_RE.match(v.strip())
    if not m:
        return None
    pre = m.group(4)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), pre.split(".") if pre else [])


def valid_semver(v):
    return parse_version(v) is not None


def _cmp_pre(a, b):
    """Compare prerelease id lists per semver §11. Empty (release) ranks higher."""
    if not a and not b:
        return 0
    if not a:
        return 1
    if not b:
        return -1
    for x, y in zip(a, b):
        xn, yn = x.isdigit(), y.isdigit()
        if xn and yn:
            c = (int(x) > int(y)) - (int(x) < int(y))
        elif xn and not yn:
            c = -1
        elif yn and not xn:
            c = 1
        else:
            c = (x > y) - (x < y)
        if c:
            return c
    return (len(a) > len(b)) - (len(a) < len(b))


def compare(v1, v2):
    for i in range(3):
        if v1[i] != v2[i]:
            return -1 if v1[i] < v2[i] else 1
    return _cmp_pre(v1[3], v2[3])


def _parse_partial(s):
    """Parse a (possibly partial / x-ranged) version.

    Returns (major, minor, patch, [pre], xlevel) where xlevel is the count of
    leading concrete numeric parts (0..3). Returns None on malformed input.
    """
    s = s.strip()
    plus = s.find("+")
    if plus != -1:
        s = s[:plus]
    pre = []
    dash = s.find("-")
    core = s
    if dash != -1:
        core, pre = s[:dash], s[dash + 1:].split(".")
    nums = []
    xlevel = 0
    saw_wild = False
    for b in core.split(".")[:3]:
        if b in ("x", "X", "*", ""):
            saw_wild = True
            nums.append(0)
        elif b.isdigit():
            if saw_wild:
                return None
            nums.append(int(b))
            xlevel += 1
        else:
            return None
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2], pre, xlevel)


def _caret(rest):
    p = _parse_partial(rest)
    if p is None:
        return None
    M, m, pa, pre, xl = p
    lower = (">=", (M, m, pa, pre))
    if M > 0:
        upper = ("<", (M + 1, 0, 0, []))
    elif m > 0:
        upper = ("<", (0, m + 1, 0, []))
    elif xl >= 3:
        upper = ("<", (0, 0, pa + 1, []))
    elif xl == 2:
        upper = ("<", (0, 1, 0, []))
    else:
        upper = ("<", (1, 0, 0, []))
    return [lower, upper]


def _tilde(rest):
    p = _parse_partial(rest)
    if p is None:
        return None
    M, m, pa, pre, xl = p
    lower = (">=", (M, m, pa, pre))
    if xl >= 2:
        upper = ("<", (M, m + 1, 0, []))
    elif xl == 1:
        upper = ("<", (M + 1, 0, 0, []))
    else:
        upper = (">=", (0, 0, 0, []))
    return [lower, upper]


def _from_partial(op, rest):
    p = _parse_partial(rest)
    if p is None:
        return None
    M, m, pa, pre, xl = p
    if xl >= 3:
        return [(op, (M, m, pa, pre))]
    if op == "=":
        if xl == 0:
            return [(">=", (0, 0, 0, []))]
        if xl == 1:
            return [(">=", (M, 0, 0, [])), ("<", (M + 1, 0, 0, []))]
        return [(">=", (M, m, 0, [])), ("<", (M, m + 1, 0, []))]
    if op == ">":
        if xl == 0:
            return [("<", (0, 0, 0, []))]
        if xl == 1:
            return [(">=", (M + 1, 0, 0, []))]
        return [(">=", (M, m + 1, 0, []))]
    if op == ">=":
        if xl == 0:
            return [(">=", (0, 0, 0, []))]
        if xl == 1:
            return [(">=", (M, 0, 0, []))]
        return [(">=", (M, m, 0, []))]
    if op == "<":
        if xl <= 1:
            return [("<", (M, 0, 0, []))]
        return [("<", (M, m, 0, []))]
    if op == "<=":
        if xl == 0:
            return [(">=", (0, 0, 0, []))]
        if xl == 1:
            return [("<", (M + 1, 0, 0, []))]
        return [("<", (M, m + 1, 0, []))]
    return None


def _expand_token(tok):
    tok = tok.strip()
    if tok in ("", "*", "x", "X"):
        return [(">=", (0, 0, 0, []))]
    if tok[0] == "^":
        return _caret(tok[1:])
    if tok[0] == "~":
        rest = tok[1:]
        if rest.startswith(">"):
            rest = rest[1:]
        return _tilde(rest)
    m = re.match(r"^(>=|<=|>|<|=)?\s*(.+)$", tok)
    if not m:
        return None
    return _from_partial(m.group(1) or "=", m.group(2).strip())


def _hyphen(lo, hi):
    a = _parse_partial(lo)
    b = _parse_partial(hi)
    if a is None or b is None:
        return None
    lower = (">=", (a[0], a[1], a[2], a[3]))
    if b[4] >= 3:
        upper = ("<=", (b[0], b[1], b[2], b[3]))
    elif b[4] == 1:
        upper = ("<", (b[0] + 1, 0, 0, []))
    else:
        upper = ("<", (b[0], b[1] + 1, 0, []))
    return [lower, upper]


def _parse_clause(part):
    part = part.strip()
    hy = re.split(r"\s+-\s+", part)
    if len(hy) == 2:
        return _hyphen(hy[0], hy[1])
    if part == "":
        return [(">=", (0, 0, 0, []))]
    comps = []
    for t in part.split():
        ex = _expand_token(t)
        if ex is None:
            return None
        comps.extend(ex)
    return comps


def parse_range(r):
    if not isinstance(r, str):
        return None
    r = r.strip() or "*"
    clauses = []
    for part in r.split("||"):
        comps = _parse_clause(part)
        if comps is None:
            return None
        clauses.append(comps)
    return clauses


def valid_range(r):
    cl = parse_range(r)
    return bool(cl)


def _test(v, op, cv):
    c = compare(v, cv)
    return {
        ">=": c >= 0,
        "<=": c <= 0,
        ">": c > 0,
        "<": c < 0,
        "=": c == 0,
    }[op]


def satisfies(version, range_str):
    v = parse_version(version)
    if v is None:
        return False
    clauses = parse_range(range_str)
    if clauses is None:
        return False
    for comps in clauses:
        if v[3]:  # prerelease versions only satisfy comparators sharing their tuple
            allowed = any(
                cv[3] and cv[0] == v[0] and cv[1] == v[1] and cv[2] == v[2]
                for _, cv in comps
            )
            if not allowed:
                continue
        if all(_test(v, op, cv) for op, cv in comps):
            return True
    return False


# ---------------------------------------------------------------------------
# Reporting

class Report:
    def __init__(self):
        self.results = []

    def pass_(self, id_, msg=""):
        self.results.append({"id": id_, "kind": "pass", "message": msg})

    def warn(self, id_, msg):
        self.results.append({"id": id_, "kind": "warn", "message": msg})

    def error(self, id_, msg):
        self.results.append({"id": id_, "kind": "error", "message": msg})

    def ok(self):
        return not any(r["kind"] == "error" for r in self.results)


# ---------------------------------------------------------------------------
# Helpers (mirror validate-module.mjs)

def safe_path_inside_root(root_abs, declared):
    """Mirror safePathInsideRoot: abs path on success, None on traversal/escape."""
    if not isinstance(declared, str) or declared == "":
        return None
    if os.path.isabs(declared):
        return None
    if ".." in re.split(r"[\\/]", declared):
        return None
    resolved = os.path.normpath(os.path.join(root_abs, declared))
    if resolved != root_abs and not resolved.startswith(root_abs + os.sep):
        return None
    if os.path.exists(resolved):
        try:
            real = os.path.realpath(resolved)
            real_root = os.path.realpath(root_abs)
            if real != real_root and not real.startswith(real_root + os.sep):
                return None
        except OSError:
            return None
    return resolved


def parse_frontmatter(content):
    """Top-level scalar keys from a `---\\n...\\n---\\n` block, or None."""
    m = re.match(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n", content)
    if not m:
        return None
    return _simple_yaml(m.group(1))


def _strip_scalar(value):
    value = value.strip()
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        return value[1:-1]
    return value


def _simple_yaml(text):
    """Parse top-level `key: value` scalar pairs (no nesting). Good enough for
    SKILL.md frontmatter and module.yaml top-level `code:`."""
    out = {}
    for line in text.splitlines():
        if not line or line[0] in " \t#-":
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = _strip_scalar(value)
        if value.startswith(">") or value.startswith("|"):
            value = ""
        out[key] = value
    return out


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Checks

def check_manifest_exists(ctx):
    p = os.path.join(ctx["root"], ".claude-plugin", "plugin.json")
    if not os.path.exists(p):
        ctx["report"].error("C01", "missing .claude-plugin/plugin.json")
        return False
    try:
        ctx["manifest"] = read_json(p)
        ctx["report"].pass_("C01", "manifest present and parses")
        return True
    except Exception as e:  # noqa: BLE001 - mirror Node's broad catch
        ctx["report"].error("C01", f"plugin.json failed to parse: {e}")
        return False


def check_required_fields(ctx):
    m = ctx["manifest"]
    missing = []
    if not isinstance(m.get("name"), str):
        missing.append("name")
    if not isinstance(m.get("version"), str):
        missing.append("version")
    if not isinstance(m.get("description"), str):
        missing.append("description")
    bmad = m.get("bmad")
    if not isinstance(bmad, dict):
        missing.append("bmad")
    else:
        if not isinstance(bmad.get("specVersion"), str):
            missing.append("bmad.specVersion")
        if not isinstance(bmad.get("code"), str):
            missing.append("bmad.code")
        compat = bmad.get("compatibility")
        if not (isinstance(compat, dict) and isinstance(compat.get("bmadMethod"), str)):
            missing.append("bmad.compatibility.bmadMethod")
    if missing:
        ctx["report"].error("C02", f"missing required fields: {', '.join(missing)}")
    else:
        ctx["report"].pass_("C02", "all required fields present")


def check_name_regex(ctx):
    name = ctx["manifest"].get("name")
    if not isinstance(name, str):
        return
    if not NAME_REGEX.match(name) or len(name) < NAME_MIN_LEN or len(name) > NAME_MAX_LEN:
        ctx["report"].error(
            "C03", f'name "{name}" must match /^[a-z][a-z0-9-]+$/ and be 3-64 chars'
        )
    else:
        ctx["report"].pass_("C03", f'name "{name}" ok')


def check_semver(ctx):
    m = ctx["manifest"]
    version = m.get("version")
    if isinstance(version, str):
        if not valid_semver(version):
            ctx["report"].error("C04a", f'version "{version}" is not valid semver')
        else:
            ctx["report"].pass_("C04a", f"version {version} ok")
    bmad = m.get("bmad") or {}
    compat = bmad.get("compatibility") or {}
    rng = compat.get("bmadMethod")
    if isinstance(rng, str):
        if not valid_range(rng):
            ctx["report"].error(
                "C04b", f'bmad.compatibility.bmadMethod "{rng}" is not a valid semver range'
            )
        else:
            ctx["report"].pass_("C04b", f'bmad.compatibility.bmadMethod "{rng}" ok')
    claude = compat.get("claudeCode")
    if claude is not None and (not isinstance(claude, str) or not valid_range(claude)):
        ctx["report"].warn(
            "C04c", "bmad.compatibility.claudeCode is set but not a valid semver range"
        )


def check_bmad_code(ctx):
    code = (ctx["manifest"].get("bmad") or {}).get("code")
    if not isinstance(code, str):
        return
    if not CODE_REGEX.match(code):
        ctx["report"].error("C05a", f'bmad.code "{code}" must match /^[a-z][a-z0-9-]{{1,31}}$/')
        return
    if code in RESERVED_CODES:
        ctx["report"].error("C05b", f'bmad.code "{code}" is reserved (spec §7.1)')
        return
    ctx["report"].pass_("C05", f'bmad.code "{code}" ok')


def collect_declared_paths(m):
    out = []

    def arr(key, val):
        if isinstance(val, list):
            for v in val:
                out.append((key, v))

    def s(key, val):
        if isinstance(val, str):
            out.append((key, val))

    arr("skills", m.get("skills"))
    arr("agents", m.get("agents"))
    arr("commands", m.get("commands"))
    s("hooks", m.get("hooks"))
    if isinstance(m.get("mcpServers"), str):
        s("mcpServers", m.get("mcpServers"))
    s("lspServers", m.get("lspServers"))
    s("settings", m.get("settings"))
    bmad = m.get("bmad") or {}
    s("bmad.moduleDefinition", bmad.get("moduleDefinition"))
    s("bmad.moduleHelpCsv", bmad.get("moduleHelpCsv"))
    arr("bmad.customize.schemas", (bmad.get("customize") or {}).get("schemas"))
    docs = bmad.get("docs")
    if isinstance(docs, dict):
        s("bmad.docs.readme", docs.get("readme"))
        s("bmad.docs.changelog", docs.get("changelog"))
        hp = docs.get("homepage")
        if isinstance(hp, str) and not re.match(r"^https?:", hp):
            s("bmad.docs.homepage", hp)
    return out


def check_paths(ctx):
    declared = collect_declared_paths(ctx["manifest"])
    all_ok = True
    for key, val in declared:
        safe = safe_path_inside_root(ctx["root"], val)
        if safe is None:
            ctx["report"].error("C07", f'{key}: "{val}" — path traversal or symlink escape')
            all_ok = False
            continue
        if not os.path.exists(safe):
            ctx["report"].error("C06", f'{key}: "{val}" — does not exist')
            all_ok = False
    if all_ok and declared:
        ctx["report"].pass_("C06", f"{len(declared)} declared paths resolve safely")


def check_skill_files(ctx):
    skills = ctx["manifest"].get("skills")
    if not isinstance(skills, list):
        return
    for rel in skills:
        skill_dir = safe_path_inside_root(ctx["root"], rel)
        if not skill_dir:
            continue
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(skill_md):
            ctx["report"].error("C08a", f'skill "{rel}" missing SKILL.md')
            continue
        with open(skill_md, "r", encoding="utf-8") as fh:
            fm = parse_frontmatter(fh.read())
        if not fm or not isinstance(fm.get("name"), str) or not isinstance(fm.get("description"), str):
            ctx["report"].error(
                "C08b", f"{rel}/SKILL.md missing or unparseable frontmatter with name+description"
            )
            continue
        basename = os.path.basename(skill_dir)
        if fm["name"] != basename:
            ctx["report"].error(
                "C09",
                f'{rel}/SKILL.md frontmatter name "{fm["name"]}" must equal dir basename "{basename}"',
            )
            continue
        ctx["report"].pass_("C08/C09", f'skill "{rel}" frontmatter ok')


def check_module_definition(ctx):
    m = ctx["manifest"]
    rel = (m.get("bmad") or {}).get("moduleDefinition")
    if not isinstance(rel, str):
        return
    abs_ = safe_path_inside_root(ctx["root"], rel)
    if not abs_ or not os.path.exists(abs_):
        return
    try:
        with open(abs_, "r", encoding="utf-8") as fh:
            parsed = _simple_yaml(fh.read())
    except Exception as e:  # noqa: BLE001
        ctx["report"].error("C10", f"{rel} failed to parse as YAML: {e}")
        return
    code = (m.get("bmad") or {}).get("code")
    if parsed.get("code") != code:
        ctx["report"].error(
            "C10", f'{rel}#code "{parsed.get("code")}" must equal bmad.code "{code}"'
        )
    else:
        ctx["report"].pass_("C10", "moduleDefinition code matches bmad.code")


def check_setup_skill_name(ctx):
    v = (ctx["manifest"].get("bmad") or {}).get("setupSkill")
    if not isinstance(v, str):
        return
    if not v.endswith("-setup"):
        ctx["report"].error("C11", f'bmad.setupSkill "{v}" must end in "-setup"')
    else:
        ctx["report"].pass_("C11", f'bmad.setupSkill "{v}" ok')


def check_hooks_file(ctx):
    rel = ctx["manifest"].get("hooks")
    if not isinstance(rel, str):
        return
    abs_ = safe_path_inside_root(ctx["root"], rel)
    if not abs_ or not os.path.exists(abs_):
        return
    try:
        parsed = read_json(abs_)
    except Exception as e:  # noqa: BLE001
        ctx["report"].error("C12a", f"{rel} failed to parse as JSON: {e}")
        return
    if not isinstance(parsed.get("hooks"), dict):
        ctx["report"].error("C12b", f'{rel} missing top-level "hooks" object')
        return
    unknown = [k for k in parsed["hooks"].keys() if k not in KNOWN_HOOK_EVENTS]
    if unknown:
        ctx["report"].warn("C12c", f"{rel} declares unknown event(s): {', '.join(unknown)}")
    else:
        ctx["report"].pass_("C12", f"{rel} ok")


def check_mcp_servers(ctx):
    v = ctx["manifest"].get("mcpServers")
    if not isinstance(v, str):
        return
    abs_ = safe_path_inside_root(ctx["root"], v)
    if not abs_ or not os.path.exists(abs_):
        return
    try:
        parsed = read_json(abs_)
    except Exception as e:  # noqa: BLE001
        ctx["report"].error("C13a", f"{v} failed to parse as JSON: {e}")
        return
    servers = parsed.get("mcpServers", parsed) if isinstance(parsed, dict) else None
    if not isinstance(servers, dict):
        ctx["report"].error("C13b", f"{v}: expected an object of server entries")
        return
    problems = 0
    for name, entry in servers.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("command"), str):
            ctx["report"].error("C13c", f'{v}#{name}: missing "command"')
            problems += 1
        elif not isinstance(entry.get("args"), list):
            ctx["report"].error("C13d", f'{v}#{name}: "args" must be an array')
            problems += 1
    if not problems:
        ctx["report"].pass_("C13", f"{v} structure ok")


def check_customize_schemas(ctx):
    schemas = ((ctx["manifest"].get("bmad") or {}).get("customize") or {}).get("schemas")
    if not isinstance(schemas, list):
        return
    for rel in schemas:
        abs_ = safe_path_inside_root(ctx["root"], rel)
        if not abs_ or not os.path.exists(abs_):
            continue
        if not _HAVE_TOML:
            ctx["report"].warn("C14", f"{rel} not validated as TOML (Python <3.11; tomllib unavailable)")
            continue
        try:
            with open(abs_, "rb") as fh:
                tomllib.load(fh)
            ctx["report"].pass_("C14", f"{rel} parses as TOML")
        except Exception as e:  # noqa: BLE001
            ctx["report"].error("C14", f"{rel} failed to parse as TOML: {e}")


def check_ignore_exclusivity(ctx):
    bmad = ctx["manifest"].get("bmad") or {}
    has_field = (bmad.get("install") or {}).get("ignore") is not None
    has_file = os.path.exists(os.path.join(ctx["root"], ".bmadignore"))
    if has_field and has_file:
        ctx["report"].error("C15", "both .bmadignore and bmad.install.ignore present — pick one")
    elif has_field or has_file:
        ctx["report"].pass_("C15", "ignore declaration is unique")


# --- Warnings ---

def warn_bmad_version(ctx):
    rng = ((ctx["manifest"].get("bmad") or {}).get("compatibility") or {}).get("bmadMethod")
    if not rng or not valid_range(rng):
        return
    if not satisfies(LATEST_KNOWN_BMAD, rng):
        ctx["report"].warn(
            "W01",
            f'bmad.compatibility.bmadMethod "{rng}" excludes latest known BMAD-METHOD {LATEST_KNOWN_BMAD}',
        )


def warn_name_prefix(ctx):
    name = ctx["manifest"].get("name")
    if isinstance(name, str) and name.startswith("bmad-"):
        ctx["report"].warn(
            "W02", f'name "{name}" uses reserved "bmad-" prefix (spec §7.2: only for verified orgs)'
        )


def warn_skill_collisions(ctx):
    skills = ctx["manifest"].get("skills")
    if not isinstance(skills, list):
        return
    for rel in skills:
        abs_ = safe_path_inside_root(ctx["root"], rel)
        if not abs_:
            continue
        skill_md = os.path.join(abs_, "SKILL.md")
        if not os.path.exists(skill_md):
            continue
        with open(skill_md, "r", encoding="utf-8") as fh:
            fm = parse_frontmatter(fh.read())
        if fm and fm.get("name") in KNOWN_OFFICIAL_SKILLS:
            ctx["report"].warn("W03", f'skill name "{fm["name"]}" collides with an official BMAD skill')


_SPDX_SNIFF = {
    "MIT": re.compile(r"MIT License", re.I),
    "Apache-2.0": re.compile(r"Apache License.*2\.0|Version 2\.0.*Apache", re.I | re.S),
    "BSD-2-Clause": re.compile(r"BSD 2-Clause", re.I),
    "BSD-3-Clause": re.compile(r"BSD 3-Clause", re.I),
    "ISC": re.compile(r"ISC License", re.I),
    "GPL-3.0": re.compile(r"GNU GENERAL PUBLIC LICENSE.*Version 3", re.I | re.S),
    "AGPL-3.0": re.compile(r"AFFERO GENERAL PUBLIC LICENSE", re.I),
}


def warn_license_spdx(ctx):
    spdx = ctx["manifest"].get("license")
    if not isinstance(spdx, str):
        return
    lic_path = os.path.join(ctx["root"], "LICENSE")
    if not os.path.exists(lic_path):
        ctx["report"].warn("W04", f'license declared "{spdx}" but no LICENSE file present')
        return
    with open(lic_path, "r", encoding="utf-8") as fh:
        head = " ".join(fh.read().split("\n")[:3])
    pat = _SPDX_SNIFF.get(spdx)
    if pat and not pat.search(head):
        ctx["report"].warn("W04", f'license SPDX "{spdx}" does not match LICENSE file content')


# ---------------------------------------------------------------------------
# Output

def print_pretty(report, module_root, json_mode):
    if json_mode:
        sys.stdout.write(
            json.dumps(
                {
                    "ok": report.ok(),
                    "moduleRoot": module_root,
                    "specVersion": SPEC_VERSION,
                    "results": report.results,
                },
                indent=2,
            )
            + "\n"
        )
        return
    use_color = sys.stdout.isatty()

    def c(code, s):
        return f"\x1b[{code}m{s}\x1b[0m" if use_color else s

    print(c("1", f"Validating {module_root}"))
    print(c("2", f"(spec {SPEC_VERSION})"))
    print("")
    for r in report.results:
        tag = {"pass": c("32", "PASS"), "warn": c("33", "WARN")}.get(r["kind"], c("31", "FAIL"))
        print(f"  [{r['id']:<9}] {tag}  {r['message']}")
    counts = {"pass": 0, "warn": 0, "error": 0}
    for r in report.results:
        counts[r["kind"]] += 1
    summary = f"{counts['pass']} pass · {counts['warn']} warn · {counts['error']} fail"
    print("")
    print(c("32", "OK " + summary) if report.ok() else c("31", "FAILED " + summary))


# ---------------------------------------------------------------------------
# CLI

def run(root):
    report = Report()
    ctx = {"root": root, "manifest": None, "report": report}
    if not check_manifest_exists(ctx):
        return report
    check_required_fields(ctx)
    check_name_regex(ctx)
    check_semver(ctx)
    check_bmad_code(ctx)
    check_paths(ctx)
    check_skill_files(ctx)
    check_module_definition(ctx)
    check_setup_skill_name(ctx)
    check_hooks_file(ctx)
    check_mcp_servers(ctx)
    check_customize_schemas(ctx)
    check_ignore_exclusivity(ctx)
    warn_bmad_version(ctx)
    warn_name_prefix(ctx)
    warn_skill_collisions(ctx)
    warn_license_spdx(ctx)
    return report


def main():
    parser = argparse.ArgumentParser(description="Validate a BMAD module plugin.json (spec §13)")
    parser.add_argument("module_root", help="Path to the module root (containing .claude-plugin/)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    root = os.path.realpath(os.path.abspath(args.module_root))
    if not os.path.isdir(root):
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    report = run(root)
    print_pretty(report, root, args.json)
    return 0 if report.ok() else 1


if __name__ == "__main__":
    sys.exit(main())
