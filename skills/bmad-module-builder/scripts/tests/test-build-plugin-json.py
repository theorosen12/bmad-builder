#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for build-plugin-json.py (shared manifest synthesizer)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
SCRIPT = SCRIPTS / "build-plugin-json.py"
VALIDATOR = SCRIPTS / "validate-plugin-json.py"


def write_skill(root: Path, rel: str, customize: bool = False):
    d = root / rel
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"---\nname: {d.name}\ndescription: A test skill here.\n---\n# {d.name}\n")
    if customize:
        (d / "customize.toml").write_text('[agent]\ncode = "x"\n')
    return d


def run(root: Path, *extra):
    cmd = [sys.executable, str(SCRIPT), str(root), *extra]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError:
        data = {"_raw": res.stdout, "_err": res.stderr}
    return res.returncode, data


def base_args(**over):
    a = ["--code", over.get("code", "thing"), "--bmad-method-range", over.get("range", ">=6.6.0")]
    if "name" in over:
        a += ["--name", over["name"]]
    if "version" in over:
        a += ["--version", over["version"]]
    if "description" in over:
        a += ["--description", over["description"]]
    return a


def make_basic_module(tmp: Path):
    """A module the synthesizer can fully resolve without args beyond identity."""
    write_skill(tmp, "skills/my-skill", customize=True)
    (tmp / "README.md").write_text("# readme\n")
    return tmp


def test_basic_synthesis():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        code, data = run(
            root, *base_args(name="acme-thing", version="1.0.0", description="A perfectly good description string."),
            "--dry-run",
        )
        assert code == 0, data
        m = data["manifest"]
        assert m["name"] == "acme-thing"
        assert m["version"] == "1.0.0"
        assert m["skills"] == ["./skills/my-skill"]
        assert m["bmad"]["code"] == "thing"
        assert m["bmad"]["specVersion"] == "1.0.0"
        assert m["bmad"]["customize"]["schemas"] == ["./skills/my-skill/customize.toml"]
        assert data["written"] is False


def test_writes_file_and_validates():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        code, data = run(
            root, *base_args(name="acme-thing", version="1.0.0", description="A perfectly good description string."),
        )
        assert code == 0 and data["written"] is True
        manifest_path = Path(t) / ".claude-plugin" / "plugin.json"
        assert manifest_path.is_file()
        # The synthesized manifest must pass the §13 validator.
        res = subprocess.run([sys.executable, str(VALIDATOR), str(root), "--json"], capture_output=True, text=True)
        out = json.loads(res.stdout)
        assert out["ok"] is True, out


def test_name_de_bmad_from_marketplace():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "skills/my-skill")
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
            "name": "bmad-acme-thing",
            "plugins": [{"name": "bmad-acme-thing", "description": "A nice long description for tests.", "version": "2.1.0"}],
        }))
        code, data = run(root, "--code", "thing", "--bmad-method-range", ">=6.6.0", "--dry-run")
        assert code == 0, data
        assert data["manifest"]["name"] == "acme-thing"
        assert data["manifest"]["version"] == "2.1.0"


def test_version_conflict_warning():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        make_basic_module(root)
        (root / "package.json").write_text(json.dumps({"version": "0.2.1", "description": "pkg description long enough."}))
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
            "plugins": [{"name": "acme-thing", "version": "0.2.0", "description": "mkt description long enough here."}],
        }))
        code, data = run(root, "--name", "acme-thing", "--code", "thing", "--bmad-method-range", ">=6.6.0", "--dry-run")
        assert code == 0
        assert data["manifest"]["version"] == "0.2.1"  # package.json wins
        assert any("version differs" in w for w in data["warnings"])


def test_description_too_short_errors():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        code, data = run(root, *base_args(name="acme-thing", version="1.0.0", description="short"), "--dry-run")
        assert code == 2
        assert data["status"] == "error"
        assert any("description" in e for e in data["errors"])


def test_reserved_code_error():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        code, data = run(root, *base_args(name="acme-thing", version="1.0.0", description="A good description here."),
                         "--code", "cis", "--dry-run")
        # --code overrides the default in base_args via later position
        assert code == 2 and data["status"] == "error"
        assert any("reserved" in e for e in data["errors"])


def test_reserved_code_prompt_needs_resolution():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        code, data = run(root, "--name", "acme-thing", "--code", "cis", "--bmad-method-range", ">=6.6.0",
                         "--description", "A good description here.", "--on-reserved", "prompt", "--dry-run")
        assert code == 3
        assert data["status"] == "needs_resolution"
        assert data["field"] == "bmad.code"
        assert data["reason"] == "reserved"


def test_bmad_name_prefix_warns_not_blocks():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        code, data = run(root, "--name", "bmad-acme-thing", "--code", "thing", "--bmad-method-range", ">=6.6.0",
                         "--description", "A good description here.", "--dry-run")
        assert code == 0
        assert any("bmad-" in w and "W02" in w for w in data["warnings"])


def test_install_ignore_discovery_default():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        (root / "docs").mkdir()
        (root / "package.json").write_text(json.dumps({"description": "pkg description long enough."}))
        (root / "CONTRIBUTING.md").write_text("x")
        code, data = run(root, "--name", "acme-thing", "--code", "thing", "--bmad-method-range", ">=6.6.0",
                         "--description", "A good description here.", "--dry-run")
        ignore = data["manifest"]["bmad"]["install"]["ignore"]
        assert "docs/**" in ignore
        assert "package.json" in ignore
        assert "node_modules/**" in ignore  # always
        assert "CONTRIBUTING.md" in ignore
        assert "tests/**" not in ignore  # no tests/ dir present


def test_bmadignore_omits_install_ignore():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        (root / ".bmadignore").write_text("docs/**\n")
        code, data = run(root, "--name", "acme-thing", "--code", "thing", "--bmad-method-range", ">=6.6.0",
                         "--description", "A good description here.", "--dry-run")
        assert code == 0
        assert "install" not in data["manifest"]["bmad"] or "ignore" not in data["manifest"]["bmad"].get("install", {})
        assert any(".bmadignore" in w for w in data["warnings"])


def test_explicit_ignore_override():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        code, data = run(root, "--name", "acme-thing", "--code", "thing", "--bmad-method-range", ">=6.6.0",
                         "--description", "A good description here.", "--ignore", "foo/**", "--ignore", "bar.txt", "--dry-run")
        assert data["manifest"]["bmad"]["install"]["ignore"] == ["foo/**", "bar.txt"]


def test_no_ignore_flag():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        (root / "docs").mkdir()
        code, data = run(root, "--name", "acme-thing", "--code", "thing", "--bmad-method-range", ">=6.6.0",
                         "--description", "A good description here.", "--no-ignore", "--dry-run")
        assert "install" not in data["manifest"]["bmad"]


def test_claude_subagents_discovered():
    with tempfile.TemporaryDirectory() as t:
        root = make_basic_module(Path(t))
        (root / "agents").mkdir()
        (root / "agents" / "reviewer.md").write_text("# reviewer\n")
        code, data = run(root, "--name", "acme-thing", "--code", "thing", "--bmad-method-range", ">=6.6.0",
                         "--description", "A good description here.", "--dry-run")
        assert data["manifest"]["agents"] == ["./agents/reviewer.md"]


def test_setup_skill_and_module_definition():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "skills/acme-setup")
        write_skill(root, "skills/acme-do")
        (root / "skills" / "acme-setup" / "assets").mkdir()
        (root / "skills" / "acme-setup" / "assets" / "module.yaml").write_text('code: thing\nname: "Acme"\n')
        code, data = run(root, "--name", "acme-thing", "--code", "thing", "--bmad-method-range", ">=6.6.0",
                         "--description", "A good description here.",
                         "--setup-skill", "acme-setup",
                         "--module-definition", "skills/acme-setup/assets/module.yaml",
                         "--post-install-skill", "acme-setup", "--dry-run")
        assert code == 0
        b = data["manifest"]["bmad"]
        assert b["setupSkill"] == "acme-setup"
        assert b["moduleDefinition"] == "skills/acme-setup/assets/module.yaml"
        assert b["install"]["postInstallSkill"] == "acme-setup"


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
