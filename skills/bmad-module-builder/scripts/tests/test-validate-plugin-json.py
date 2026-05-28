#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for validate-plugin-json.py (spec §13 port).

Two layers:
  - subprocess tests build temp modules and assert on the `--json` result IDs;
  - in-process imports exercise the hand-rolled semver engine directly.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
SCRIPT = SCRIPTS / "validate-plugin-json.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_plugin_json", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


VPJ = _load_module()


# --- fixtures ---------------------------------------------------------------

def write_skill(root: Path, rel: str, name: str = None, description: str = "A test skill."):
    d = root / rel
    d.mkdir(parents=True, exist_ok=True)
    fm_name = name if name is not None else d.name
    (d / "SKILL.md").write_text(
        f"---\nname: {fm_name}\ndescription: {description}\n---\n# {d.name}\n"
    )
    return d


def make_module(tmp: Path, manifest: dict, skills: dict | None = None):
    """Create a module root with .claude-plugin/plugin.json and skill dirs.

    `skills` maps a skill rel-path -> frontmatter name (None = use basename)."""
    (tmp / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (tmp / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, indent=2))
    for rel, fm_name in (skills or {}).items():
        write_skill(tmp, rel, fm_name)
    return tmp


def base_manifest(**over):
    m = {
        "name": "acme-thing",
        "version": "0.1.0",
        "description": "A perfectly fine description for testing.",
        "license": "MIT",
        "skills": ["./skills/acme-thing"],
        "bmad": {
            "specVersion": "1.0.0",
            "code": "thing",
            "compatibility": {"bmadMethod": ">=6.6.0"},
        },
    }
    m.update(over)
    return m


def run_json(module_root: Path):
    res = subprocess.run(
        [sys.executable, str(SCRIPT), str(module_root), "--json"],
        capture_output=True,
        text=True,
    )
    data = json.loads(res.stdout)
    ids = {(r["id"], r["kind"]) for r in data["results"]}
    return res.returncode, data, ids


def has(ids, id_, kind):
    return (id_, kind) in ids


# --- subprocess tests -------------------------------------------------------

def test_minimal_valid_passes():
    with tempfile.TemporaryDirectory() as t:
        root = make_module(Path(t), base_manifest(), {"skills/acme-thing": None})
        code, data, ids = run_json(root)
        assert code == 0, data
        assert data["ok"] is True
        assert has(ids, "C05", "pass")
        assert not any(k == "error" for _, k in ids)


def test_missing_manifest_c01():
    with tempfile.TemporaryDirectory() as t:
        code, data, ids = run_json(Path(t))
        assert code == 1
        assert has(ids, "C01", "error")


def test_unparseable_manifest_c01():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin" / "plugin.json").write_text("{ not json ]")
        code, data, ids = run_json(root)
        assert code == 1 and has(ids, "C01", "error")


def test_missing_required_c02():
    with tempfile.TemporaryDirectory() as t:
        m = base_manifest()
        del m["version"]
        del m["bmad"]["compatibility"]
        root = make_module(Path(t), m, {"skills/acme-thing": None})
        code, data, ids = run_json(root)
        assert has(ids, "C02", "error")


def test_bad_name_c03():
    with tempfile.TemporaryDirectory() as t:
        root = make_module(Path(t), base_manifest(name="Bad_Name"), {"skills/acme-thing": None})
        _, _, ids = run_json(root)
        assert has(ids, "C03", "error")


def test_bad_version_c04a():
    with tempfile.TemporaryDirectory() as t:
        root = make_module(Path(t), base_manifest(version="not.semver"), {"skills/acme-thing": None})
        _, _, ids = run_json(root)
        assert has(ids, "C04a", "error")


def test_bad_range_c04b():
    with tempfile.TemporaryDirectory() as t:
        m = base_manifest()
        m["bmad"]["compatibility"]["bmadMethod"] = "garbage!!"
        root = make_module(Path(t), m, {"skills/acme-thing": None})
        _, _, ids = run_json(root)
        assert has(ids, "C04b", "error")


def test_reserved_code_c05b():
    with tempfile.TemporaryDirectory() as t:
        m = base_manifest()
        m["bmad"]["code"] = "cis"
        root = make_module(Path(t), m, {"skills/acme-thing": None})
        _, _, ids = run_json(root)
        assert has(ids, "C05b", "error")


def test_bad_code_regex_c05a():
    with tempfile.TemporaryDirectory() as t:
        m = base_manifest()
        m["bmad"]["code"] = "Bad-CODE"
        root = make_module(Path(t), m, {"skills/acme-thing": None})
        _, _, ids = run_json(root)
        assert has(ids, "C05a", "error")


def test_nonexistent_path_c06():
    with tempfile.TemporaryDirectory() as t:
        m = base_manifest(skills=["./skills/missing"])
        root = make_module(Path(t), m)  # no skill dir created
        _, _, ids = run_json(root)
        assert has(ids, "C06", "error")


def test_path_traversal_c07():
    with tempfile.TemporaryDirectory() as t:
        m = base_manifest(skills=["../escape"])
        root = make_module(Path(t), m, {"skills/acme-thing": None})
        _, _, ids = run_json(root)
        assert has(ids, "C07", "error")


def test_skill_missing_skillmd_c08a():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        make_module(root, base_manifest())
        (root / "skills" / "acme-thing").mkdir(parents=True)  # dir but no SKILL.md
        _, _, ids = run_json(root)
        assert has(ids, "C08a", "error")


def test_frontmatter_name_mismatch_c09():
    with tempfile.TemporaryDirectory() as t:
        root = make_module(Path(t), base_manifest(), {"skills/acme-thing": "wrong-name"})
        _, _, ids = run_json(root)
        assert has(ids, "C09", "error")


def test_module_definition_code_mismatch_c10():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        m = base_manifest()
        m["bmad"]["moduleDefinition"] = "module.yaml"
        make_module(root, m, {"skills/acme-thing": None})
        (root / "module.yaml").write_text('code: different\nname: "x"\n')
        _, _, ids = run_json(root)
        assert has(ids, "C10", "error")


def test_module_definition_code_match_c10_pass():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        m = base_manifest()
        m["bmad"]["moduleDefinition"] = "module.yaml"
        make_module(root, m, {"skills/acme-thing": None})
        (root / "module.yaml").write_text('code: thing\nname: "x"\n')
        _, _, ids = run_json(root)
        assert has(ids, "C10", "pass")


def test_setup_skill_name_c11():
    with tempfile.TemporaryDirectory() as t:
        m = base_manifest()
        m["bmad"]["setupSkill"] = "acme-thing"  # missing -setup
        root = make_module(Path(t), m, {"skills/acme-thing": None})
        _, _, ids = run_json(root)
        assert has(ids, "C11", "error")


def test_hooks_unknown_event_c12c():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        m = base_manifest(hooks="./hooks/hooks.json")
        make_module(root, m, {"skills/acme-thing": None})
        (root / "hooks").mkdir()
        (root / "hooks" / "hooks.json").write_text(json.dumps({"hooks": {"BogusEvent": []}}))
        _, _, ids = run_json(root)
        assert has(ids, "C12c", "warn")


def test_mcp_missing_command_c13c():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        m = base_manifest(mcpServers="./.mcp.json")
        make_module(root, m, {"skills/acme-thing": None})
        (root / ".mcp.json").write_text(json.dumps({"mcpServers": {"x": {"args": []}}}))
        _, _, ids = run_json(root)
        assert has(ids, "C13c", "error")


def test_customize_bad_toml_c14():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        m = base_manifest()
        m["bmad"]["customize"] = {"schemas": ["./bad.toml"]}
        make_module(root, m, {"skills/acme-thing": None})
        (root / "bad.toml").write_text("this is = = not toml")
        _, _, ids = run_json(root)
        assert has(ids, "C14", "error")


def test_ignore_exclusivity_c15():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        m = base_manifest()
        m["bmad"]["install"] = {"ignore": ["docs/**"]}
        make_module(root, m, {"skills/acme-thing": None})
        (root / ".bmadignore").write_text("docs/**\n")
        _, _, ids = run_json(root)
        assert has(ids, "C15", "error")


def test_w01_excludes_latest():
    with tempfile.TemporaryDirectory() as t:
        m = base_manifest()
        m["bmad"]["compatibility"]["bmadMethod"] = ">=6.0.0 <6.5.0"
        root = make_module(Path(t), m, {"skills/acme-thing": None})
        code, data, ids = run_json(root)
        assert code == 0  # warning only
        assert has(ids, "W01", "warn")


def test_w02_bmad_prefix():
    with tempfile.TemporaryDirectory() as t:
        root = make_module(Path(t), base_manifest(name="bmad-acme-thing"), {"skills/acme-thing": None})
        _, _, ids = run_json(root)
        assert has(ids, "W02", "warn")


def test_w04_license_mismatch():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        make_module(root, base_manifest(license="Apache-2.0"), {"skills/acme-thing": None})
        (root / "LICENSE").write_text("MIT License\n\nCopyright ...\n")
        _, _, ids = run_json(root)
        assert has(ids, "W04", "warn")


# --- semver engine ----------------------------------------------------------

def test_valid_semver():
    assert VPJ.valid_semver("1.2.3")
    assert VPJ.valid_semver("0.0.1")
    assert VPJ.valid_semver("1.2.3-rc.1")
    assert not VPJ.valid_semver("1.2")
    assert not VPJ.valid_semver("v1.2.3")
    assert not VPJ.valid_semver("1.2.3.4")


def test_valid_range():
    assert VPJ.valid_range(">=6.6.0 <7.0.0")
    assert VPJ.valid_range(">=6.6.0")
    assert VPJ.valid_range("^1.2.3")
    assert VPJ.valid_range("~1.2")
    assert VPJ.valid_range("1.x")
    assert VPJ.valid_range("*")
    assert VPJ.valid_range("1.2.3 || >=2.0.0")
    assert not VPJ.valid_range("!!nope")


def test_satisfies_range():
    assert VPJ.satisfies("6.7.1", ">=6.6.0 <7.0.0")
    assert not VPJ.satisfies("7.0.0", ">=6.6.0 <7.0.0")
    assert not VPJ.satisfies("6.5.9", ">=6.6.0 <7.0.0")
    assert VPJ.satisfies("6.7.1", ">=6.6.0")
    assert VPJ.satisfies("6.4.0", ">=6.0.0 <6.5.0")


def test_satisfies_caret_tilde():
    assert VPJ.satisfies("1.4.0", "^1.2.3")
    assert not VPJ.satisfies("2.0.0", "^1.2.3")
    assert VPJ.satisfies("0.2.9", "^0.2.3")
    assert not VPJ.satisfies("0.3.0", "^0.2.3")
    assert VPJ.satisfies("1.2.9", "~1.2.3")
    assert not VPJ.satisfies("1.3.0", "~1.2.3")


def test_satisfies_or_clause():
    assert VPJ.satisfies("3.0.0", "1.2.3 || >=2.0.0")
    assert VPJ.satisfies("1.2.3", "1.2.3 || >=2.0.0")
    assert not VPJ.satisfies("1.5.0", "1.2.3 || >=2.0.0")


def test_prerelease_excluded_by_default():
    # node-semver excludes prereleases unless the comparator tuple shares them
    assert not VPJ.satisfies("7.0.0-rc.1", ">=6.6.0 <7.0.0")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR: {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
