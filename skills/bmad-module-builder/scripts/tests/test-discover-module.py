#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for discover-module.py (read-only inventory + data-quality scan)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "discover-module.py"

CANONICAL_HEADER = (
    "module,skill,display-name,menu-code,description,action,args,phase,"
    "preceded-by,followed-by,required,output-location,outputs\n"
)


def write_skill(root: Path, rel: str, fm_name=None, customize=None):
    d = root / rel
    d.mkdir(parents=True, exist_ok=True)
    name = fm_name if fm_name is not None else d.name
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: A test skill.\n---\n# {d.name}\n")
    if customize is not None:
        (d / "customize.toml").write_text(customize)
    return d


def run(root: Path, *extra):
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--module-root", str(root), *extra],
        capture_output=True, text=True,
    )
    return res.returncode, json.loads(res.stdout)


def dq_codes(data):
    return [q["code"] for q in data["data_quality"]]


def test_basic_skill_discovery():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "src/skills/my-agent", customize='[agent]\ncode = "x"\n')
        write_skill(root, "src/skills/my-flow", customize='[workflow]\nname = "y"\n')
        write_skill(root, "src/skills/plain")
        code, data = run(root)
        assert code == 0
        assert data["counts"]["skills"] == 3
        assert data["counts"]["customize_schemas"] == 2
        kinds = {s["basename"]: s["customize_kind"] for s in data["skills"]}
        assert kinds["my-agent"] == "agent"
        assert kinds["my-flow"] == "workflow"
        assert kinds["plain"] == "none"
        agents = {s["basename"]: s["is_persona_agent"] for s in data["skills"]}
        assert agents["my-agent"] is True
        assert agents["my-flow"] is False


def test_reserved_code_and_empty_description():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "src/skills/s1")
        (root / "src").mkdir(exist_ok=True)
        (root / "src" / "module.yaml").write_text('code: cis\nname: "X"\ndescription: ""\n')
        code, data = run(root)
        assert "reserved-code" in dq_codes(data)
        assert "empty-description" in dq_codes(data)
        assert data["identity"]["code_reserved"] is True


def test_orphan_and_missing_csv_rows():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "src/skills/real-skill")  # non-agent, no CSV row
        write_skill(root, "src/skills/agent-foo", customize='[agent]\ncode="a"\n')  # agent, no row -> info
        (root / "src" / "module.yaml").write_text('code: ok\nname: "X"\ndescription: "desc here long enough"\n')
        (root / "src" / "module-help.csv").write_text(
            CANONICAL_HEADER
            + "X,ghost-skill,Ghost,GH,does,run,,anytime,,,false,output_folder,thing\n"
        )
        code, data = run(root)
        codes = dq_codes(data)
        assert "orphan-csv-row" in codes  # ghost-skill not on disk
        assert "missing-csv-row" in codes  # real-skill has no row
        assert "agent-no-capability-row" in codes  # agent-foo info, not high


def test_csv_header_mismatch():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "src/skills/s1")
        (root / "src" / "module.yaml").write_text('code: ok\nname: "X"\ndescription: "desc long enough here"\n')
        # legacy header with after/before instead of preceded-by/followed-by
        (root / "src" / "module-help.csv").write_text(
            "module,skill,display-name,menu-code,description,action,args,phase,after,before,required,output-location,outputs\n"
            "X,s1,S1,S1,does,run,,anytime,,,false,output_folder,thing\n"
        )
        code, data = run(root)
        assert "csv-header-mismatch" in dq_codes(data)
        assert data["module_help_csv"]["header_matches_canonical"] is False


def test_frontmatter_name_mismatch():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "src/skills/s1", fm_name="not-s1")
        code, data = run(root)
        assert "frontmatter-name-mismatch" in dq_codes(data)


def test_bmad_prefixes():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "src/skills/bmad-x-foo")
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
            "name": "bmad-x", "plugins": [{"name": "bmad-x"}],
        }))
        code, data = run(root)
        codes = dq_codes(data)
        assert "bmad-name-prefix" in codes
        assert "bmad-skill-names" in codes
        assert data["identity"]["name_candidate"] == "x"


def test_required_files_and_spdx():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "src/skills/s1")
        (root / "README.md").write_text("# r\n")
        (root / "LICENSE").write_text("MIT License\n\nCopyright\n")
        (root / "CHANGELOG.md").write_text("# changelog\n")
        code, data = run(root)
        rf = data["required_files"]
        assert rf["readme"] and rf["license"] and rf["changelog"]
        assert rf["license_spdx_sniff"] == "MIT"


def test_claude_subagents_and_roster():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "src/skills/s1")
        (root / "agents").mkdir()
        (root / "agents" / "rev.md").write_text("# rev\n")
        (root / "src" / "module.yaml").write_text(
            'code: ok\nname: "X"\ndescription: "long enough description"\n'
            "agents:\n  - code: foo\n    name: Foo\n  - code: bar\n    name: Bar\n"
        )
        code, data = run(root)
        assert data["claude_subagents"] == ["./agents/rev.md"]
        assert data["module_definition"]["agent_roster"] == ["foo", "bar"]


def test_suggested_code_from_clean_name():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        write_skill(root, "src/skills/s1")
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
            "plugins": [{"name": "acme-toolkit"}],
        }))
        code, data = run(root)
        assert data["identity"]["suggested_code"] == "acme-toolkit"
        assert data["identity"]["name_warns_bmad_prefix"] is False


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
