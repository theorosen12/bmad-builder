---
name: bmad-module-migrator
description: Converts an existing BMB-built BMad module to the new community module format (BMAD Module Manifest Spec v1.0.0) by synthesizing a canonical .claude-plugin/plugin.json. Use when the user asks to 'migrate module', 'convert module to plugin.json', 'convert to the new marketplace format', or 'update a module to the community format'.
---

# BMad Module Migrator

## Overview

This skill converts a module that was built around `module.yaml` + `module-help.csv` (the BMB toolkit's historical layout, optionally with a legacy `.claude-plugin/marketplace.json`) into the **new community module format** defined by the **BMAD Module Manifest Spec v1.0.0**. The conversion adds a canonical `.claude-plugin/plugin.json` manifest that both Claude Code's plugin marketplace and BMAD-METHOD's `bmad-module` install skill read.

**The migration is non-destructive and mostly additive.** `module.yaml`, `module-help.csv`, and every `customize.toml` **carry over unchanged** — `plugin.json` is *additional* static metadata that points at them. Files are never moved. The only in-place content edit this skill ever proposes is changing `module.yaml`'s `code:` line when a reserved `bmad.code` must be remapped (spec §13 check C10), and it always confirms that edit first.

If you are building a **brand-new** module, you don't need this skill — `bmad-module-builder`'s Create Module path already emits the new format.

**Args:** Accepts a path to the module root (default: cwd) and `--headless` / `-H` for non-interactive operation (hard-errors on a reserved `bmad.code` since it cannot prompt for a remap).

## On Activation

Load available config from `{project-root}/_bmad/config.yaml` and `{project-root}/_bmad/config.user.yaml` (root level and `bmb` section). If neither exists, fall back to `{project-root}/_bmad/bmb/config.yaml`. Use sensible defaults for anything not configured (e.g. `{bmad_builder_reports}` for the optional migration report).

**Locate the shared tooling.** The synthesizer, validator, and discovery engines live in the sibling `bmad-module-builder` skill so the builder and migrator share one source of truth. Resolve the builder scripts directory:

1. Default: `../bmad-module-builder/scripts/` relative to this skill's directory (the two skills are normally siblings under `skills/`).
2. If that directory does not exist, search the project for a `bmad-module-builder/scripts/build-plugin-json.py`, and if still not found, ask the user for the path to the `bmad-module-builder` skill.

Throughout this skill, `{bmb_scripts}` refers to that resolved directory. The migrator's own script is at `./scripts/scaffold-missing-files.py`.

## Routing

Detect the user's intent:

- **Migrate / Convert** keywords, or a path to a module root → Load `./references/migrate-module.md` and follow the 11-stage procedure.
- **Unclear** → Confirm: "I'll convert an existing BMB module to the new community `plugin.json` format. This is non-destructive — your `module.yaml`, `module-help.csv`, and `customize.toml` files stay exactly as they are. What's the path to the module root?" Then load `./references/migrate-module.md`.

If `--headless` / `-H` is passed, run the procedure non-interactively per the Headless Mode section of `migrate-module.md`.

## Supporting references

- `./references/migrate-module.md` — the end-to-end migration procedure (load this to run a migration).
- `./references/identity-mapping.md` — how to derive `name` and `bmad.code`, resolve reserved codes and `bmad-` prefixes.
- `./references/reconcile-marketplace.md` — how a legacy `marketplace.json` maps to `plugin.json`, including multi-plugin repos.

## Related

For building new modules from scratch, see the sibling **`bmad-module-builder`** skill (Ideate / Create / Validate Module). The builder's Create Module path now emits `plugin.json` directly, so newly built modules do not need this migrator.
