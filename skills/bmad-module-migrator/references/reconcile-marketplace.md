# Reconciling `marketplace.json` → `plugin.json`

A module migrating from the old flow may already ship `.claude-plugin/marketplace.json`. This note explains how it maps to the new `plugin.json` and what to do with it.

## The two files are not the same thing

Per the migration guide (spec repo `docs/migrating-from-old-marketplace.md` §3):

- **`marketplace.json`** is a *repo-level index* that lists one or more plugins for cross-tool discovery (the interim `--custom-source` flow). Its shape is `{ name, owner, license, homepage, repository, keywords, plugins: [ { name, source, description, version, author, skills } ] }`.
- **`plugin.json`** is the *per-module manifest* the current spec defines. It is what the `bmad-module` install skill and `validate-module.mjs` read. **Every module needs one.**

A single-module repo needs only `plugin.json`.

## Field mapping

`build-plugin-json.py` reads `marketplace.json` automatically and applies these mappings (each with a fallback to `package.json`):

| `marketplace.json` | `plugin.json` |
|---|---|
| `plugins[0].name` (de-`bmad-`'d) | `name` (unless `--name` given) |
| `plugins[0].version` | `version` (after `--version` / `package.json`) |
| `plugins[0].description` | `description` |
| `plugins[0].author` / top-level `owner` | `author` |
| top-level `repository` | `repository` |
| top-level `license` | `license` |
| top-level `homepage` | `homepage` |
| top-level `keywords` | `keywords` |
| `plugins[0].skills` | reconciled against filesystem `skills[]` (see below) |

`bmad.code`, `bmad.compatibility`, `bmad.category`, `bmad.moduleDefinition`, and `bmad.moduleHelpCsv` have **no** equivalent in `marketplace.json` — they come from CLI args and discovery.

## Skills reconciliation

`plugin.json`'s `skills[]` is taken from **filesystem truth** — every directory containing a `SKILL.md` — not copied from `marketplace.json`. The synthesizer compares the two and emits a warning if they differ (a skill on disk that the old index missed, or an index entry whose directory is gone). Review such warnings: a "marketplace only" entry usually means a stale index row (often the same root cause as a `data_quality` orphan-CSV-row), and an "on disk only" entry means a skill the old index never listed.

## Single-plugin repo (the common case)

`plugin.json` supersedes `marketplace.json`. Migration is non-destructive, so **leave `marketplace.json` in place** but stop relying on it. In the migration report, recommend the author delete it (or keep only if they intend multi-plugin discovery) once they've confirmed the new install flow works. Leaving it does not break validation — `validate-module.mjs` ignores `marketplace.json` entirely.

## Multi-plugin repo

If one repository publishes several modules, keep `marketplace.json` as the repo-level index and give **each** module its own `plugin.json` under that module's subtree. Run `build-plugin-json.py` once per module, pointing `--module-definition` / `--module-help-csv` and the implicit skills discovery at each module's directory. Each module validates independently with `validate-module.mjs <module-subdir>`.
