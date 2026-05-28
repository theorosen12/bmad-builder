# Identity Mapping

How to derive a module's new-format identity (`name` and `bmad.code`) and resolve the two common snags: reserved codes and `bmad-` name prefixes. The spec keeps `name` and `bmad.code` **intentionally distinct** (spec §4): `name` is the **global** identifier (Claude marketplace ID and `bmad-module install` source); `bmad.code` is the **workspace-local** install directory under `_bmad/<code>/`. They MAY share a value but usually shouldn't — `name` is verbose, `code` is short.

## Deriving `name`

`name` MUST match `^[a-z][a-z0-9-]+$`, be 3–64 chars, and be globally unique across the module ecosystem.

Source order:

1. The user's explicit choice.
2. `discover-module.py` → `identity.name_candidate` — the existing `marketplace.json` plugin/repo name with any leading `bmad-` stripped.
3. A kebab-case of `module.yaml`'s `name`.

If the resulting `name` starts with `bmad-`, warn (validator W02; spec §7.2): the `bmad-` prefix is reserved for `bmad-code-org` and verified-partner orgs. Community modules SHOULD drop it. Enforcement is social, not technical — the manifest still validates with a warning — but recommend a non-`bmad-` name unless the user is publishing under a verified org.

## Deriving `bmad.code`

`bmad.code` MUST match `^[a-z][a-z0-9-]{1,31}$` and MUST NOT be a reserved value (spec §7.1):

> **Official modules:** `core`, `bmm`, `bmb`, `cis`, `gds`, `tea`, `wds`, `automator`
> **System directories:** `_config`, `_memory`, `custom`
> **Component directory names:** `agents`, `hooks`, `config`, `commands`, `skills`

If the module's current `module.yaml` `code:` is reserved, it MUST be remapped. Pick a short, memorable, non-reserved code. Good remaps keep the module recognizable:

- Expand the acronym slightly: `cis` (reserved) → `cisuite` (Creative Innovation Suite).
- Add a scope suffix: `tea` (reserved) → `teakit`.
- Use a vendor prefix: `gds` (reserved) → `acmegds`.

Avoid codes that merely re-add a reserved value as a substring if it reduces clarity; aim for something a user will recognize in `_bmad/<code>/`.

`discover-module.py` provides `identity.suggested_code`, but it favors a literal de-`bmad-` name (which can be verbose). Prefer a concise human-chosen code over the literal suggestion when the suggestion is long.

## The C10 coupling (critical)

Once you choose a `bmad.code` that differs from `module.yaml`'s `code:`, spec check **C10** requires them to match: *if `bmad.moduleDefinition` resolves, the YAML's `code:` MUST equal `bmad.code`*. So a remap forces a one-line edit to `module.yaml`:

```
code: cis        →    code: cisuite
```

This is the **only** in-place content edit the migrator makes. Confirm it explicitly. It changes the install directory and config key (`_bmad/cis/` → `_bmad/cisuite/`), so:

- Existing installs under the old code are not touched until users reinstall.
- Document the change in the CHANGELOG so users know their install directory and any `_bmad/<old>/` config path moved.

## `bmad-` skill-name prefixes (defer, don't rename)

Many BMB modules name their skills `bmad-<code>-<role>` (e.g. `bmad-cis-agent-storyteller`). The validator warns (W02/W03) when a skill name uses the `bmad-` prefix or collides with an official BMAD skill. **Do not rename skills during migration** — a rename cascades into the roster `code`s in `module.yaml`, every `customize.toml` `skill=` menu entry, and each `SKILL.md` frontmatter `name` (which must equal its directory basename, check C09). That is high blast-radius and orthogonal to adding a manifest. Flag it as future cleanup in the migration report instead.
