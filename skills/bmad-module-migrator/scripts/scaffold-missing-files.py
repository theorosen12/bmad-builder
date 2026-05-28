#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Idempotently add the spec-required module-root files that are missing.

Spec §11 requires README.md and LICENSE at the module root and recommends
CHANGELOG.md. This script creates ONLY the ones that are absent, filling
templates from ../assets/. It NEVER overwrites an existing file — migration is
non-destructive. Run with --dry-run to preview.

  python3 scaffold-missing-files.py --module-root R --name acme-thing \\
      --code thing --display-name "Acme Thing" --description "..." \\
      --author "Acme Corp" --license MIT --version 0.1.0
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LICENSE_TEMPLATES = {"MIT": "MIT.txt", "Apache-2.0": "Apache-2.0.txt"}


def fill(text: str, ctx: dict) -> str:
    for key, value in ctx.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def main() -> int:
    p = argparse.ArgumentParser(description="Add missing README/LICENSE/CHANGELOG (non-destructive)")
    p.add_argument("--module-root", required=True)
    p.add_argument("--name", default="")
    p.add_argument("--code", default="")
    p.add_argument("--display-name", dest="display_name", default="")
    p.add_argument("--description", default="")
    p.add_argument("--author", default="")
    p.add_argument("--license", dest="license_id", default="MIT")
    p.add_argument("--version", default="0.1.0")
    p.add_argument("--repository", default="")
    p.add_argument("--year", default=str(datetime.date.today().year))
    p.add_argument("--assets-base", default=str(ASSETS), help="override template dir (tests/relocation)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    root = Path(args.module_root).resolve()
    assets = Path(args.assets_base)
    if not root.is_dir():
        print(json.dumps({"status": "error", "message": f"Not a directory: {root}"}))
        return 2

    ctx = {
        "NAME": args.name,
        "CODE": args.code,
        "DISPLAY_NAME": args.display_name or args.name,
        "DESCRIPTION": args.description,
        "AUTHOR": args.author,
        "LICENSE": args.license_id,
        "VERSION": args.version,
        "REPOSITORY": args.repository,
        "YEAR": args.year,
    }

    created, skipped, warnings = [], [], []

    def emit(rel_target: str, template_path: Path):
        dst = root / rel_target
        if dst.exists():
            skipped.append(rel_target)
            return
        if not template_path.is_file():
            warnings.append(f"template missing for {rel_target}: {template_path}")
            return
        content = fill(template_path.read_text(encoding="utf-8"), ctx)
        if not args.dry_run:
            dst.write_text(content, encoding="utf-8")
        created.append(rel_target)

    # README.md (required)
    emit("README.md", assets / "README-template.md")

    # LICENSE (required) — only if we have a template for the declared SPDX id
    lic_template = LICENSE_TEMPLATES.get(args.license_id)
    if (root / "LICENSE").exists():
        skipped.append("LICENSE")
    elif lic_template:
        emit("LICENSE", assets / "LICENSE-templates" / lic_template)
    else:
        warnings.append(
            f'no LICENSE template for SPDX "{args.license_id}"; add a LICENSE file manually (spec §11 requires one)'
        )

    # CHANGELOG.md (recommended)
    emit("CHANGELOG.md", assets / "CHANGELOG-template.md")

    print(json.dumps({
        "status": "success",
        "module_root": str(root),
        "dry_run": args.dry_run,
        "files_created": created,
        "files_skipped": skipped,
        "warnings": warnings,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
