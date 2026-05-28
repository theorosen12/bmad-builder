#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for scaffold-missing-files.py (non-destructive README/LICENSE/CHANGELOG)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scaffold-missing-files.py"


def run(root: Path, *extra):
    cmd = [
        sys.executable, str(SCRIPT),
        "--module-root", str(root),
        "--name", "acme-thing", "--code", "thing",
        "--display-name", "Acme Thing", "--description", "An acme thing module.",
        "--author", "Acme Corp", "--license", "MIT", "--version", "0.1.0",
        "--repository", "https://github.com/acme/acme-thing",
        *extra,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, json.loads(res.stdout)


def test_creates_all_when_absent():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        code, data = run(root)
        assert code == 0
        assert set(data["files_created"]) == {"README.md", "LICENSE", "CHANGELOG.md"}
        assert (root / "README.md").is_file()
        assert (root / "LICENSE").is_file()
        assert (root / "CHANGELOG.md").is_file()
        # Templating happened
        readme = (root / "README.md").read_text()
        assert "Acme Thing" in readme
        assert "_bmad/thing/" in readme
        assert "{{" not in readme
        lic = (root / "LICENSE").read_text()
        assert lic.startswith("MIT License")
        assert "Acme Corp" in lic


def test_skips_existing_never_overwrites():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        (root / "README.md").write_text("MY OWN README\n")
        (root / "LICENSE").write_text("MY OWN LICENSE\n")
        code, data = run(root)
        assert code == 0
        assert "README.md" in data["files_skipped"]
        assert "LICENSE" in data["files_skipped"]
        assert "CHANGELOG.md" in data["files_created"]
        # untouched
        assert (root / "README.md").read_text() == "MY OWN README\n"
        assert (root / "LICENSE").read_text() == "MY OWN LICENSE\n"


def test_dry_run_writes_nothing():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        code, data = run(root, "--dry-run")
        assert code == 0
        assert data["dry_run"] is True
        assert set(data["files_created"]) == {"README.md", "LICENSE", "CHANGELOG.md"}
        assert not (root / "README.md").exists()
        assert not (root / "LICENSE").exists()


def test_apache_license_template():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        cmd = [
            sys.executable, str(SCRIPT), "--module-root", str(root),
            "--name", "acme", "--code", "acme", "--license", "Apache-2.0",
            "--author", "Acme Corp",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(res.stdout)
        assert "LICENSE" in data["files_created"]
        lic = (root / "LICENSE").read_text()
        assert "Apache License" in lic
        assert "Acme Corp" in lic


def test_unknown_license_warns_no_license_file():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        cmd = [
            sys.executable, str(SCRIPT), "--module-root", str(root),
            "--name", "acme", "--code", "acme", "--license", "GPL-3.0",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(res.stdout)
        assert "LICENSE" not in data["files_created"]
        assert not (root / "LICENSE").exists()
        assert any("GPL-3.0" in w for w in data["warnings"])


def test_all_present_skips_all():
    """The CIS case: README/LICENSE/CHANGELOG already exist -> everything skipped."""
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        (root / "README.md").write_text("r\n")
        (root / "LICENSE").write_text("MIT License\n")
        (root / "CHANGELOG.md").write_text("c\n")
        code, data = run(root)
        assert code == 0
        assert data["files_created"] == []
        assert set(data["files_skipped"]) == {"README.md", "LICENSE", "CHANGELOG.md"}


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
