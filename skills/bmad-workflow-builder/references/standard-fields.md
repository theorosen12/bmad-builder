# Standard Fields and Naming Conventions

Frontmatter, body fields, stage naming, hook naming, and the customize.toml field conventions for skills the builder produces. Stage names are descriptive and unnumbered everywhere, matching the no-numbered-prefix rule.

## Frontmatter fields

Only these two fields go in the YAML frontmatter block:

| Field | Description | Example |
| --- | --- | --- |
| `name` | Full skill name, hyphen-case, same as the folder name | `validate-json`, `cis-brainstorm` |
| `description` | A 5-8 word summary, then a trigger clause naming what the user says | See Description Format below |

Nothing else belongs in frontmatter. Role, stages, hooks, and config all live in the body or in customize.toml.

## Body fields

These describe the skill inside SKILL.md, never in frontmatter:

| Field | Description | Example |
| --- | --- | --- |
| `role-guidance` | A brief expertise primer | "Act as a senior DevOps engineer" |
| `module-code` | Module code, only when the skill ships inside a module | `bmb`, `cis` |
| `input-format` | What the skill accepts | JSON file path, stdin text |
| `output-format` | What the skill returns | Validated JSON, error report |
| `composability` | How other skills call this one | "Called by quality scanners for validation" |

## Stage naming

Stages get descriptive, unnumbered names that say what the stage is for. Numbered prefixes are forbidden because they imply a fixed order the model must march through, they break under context compaction when a stage references SKILL.md, and they fight the outcome-driven shape the builder teaches. Name the stage by its goal and let the routing or the prose carry the order where order actually matters.

| Use | Not |
| --- | --- |
| `discover`, `plan`, `build` | `01-discover`, `02-plan`, `03-build` |
| `gather-input`, `draft`, `finalize` | `step-1-gather`, `step-2-draft` |

The same rule covers stage files on disk: a stage file is `discover.md`, not `01-discover.md`. When a stage genuinely must precede another (a later stage consumes an earlier stage's output), state the dependency in the prose rather than encoding it in a number, so the constraint is explicit and the name stays descriptive.

A simple utility usually needs no stages at all; it does one deterministic thing and returns. Reach for named stages only when the work has distinct phases a reader needs to navigate.

## Hook naming

Hook points use the `on_<event>` form, where the event names the moment the hook fires. The hook value is a prompt string or a command the skill runs at that point, empty by default.

| Hook | Fires |
| --- | --- |
| `on_complete` | After the skill finishes its work |
| `on_start` | Before the skill's first stage runs |
| `on_error` | When the skill hits an unrecoverable error |

Keep hooks to real moments the skill reaches. Do not invent hook points for events the skill never produces.

## customize.toml field conventions

customize.toml is the only customizability mechanism, emitted only when the author accepts the customization offer (default no). The file sits next to SKILL.md and the resolver merges it with team and user override files at activation. The `references/customize-toml-guide.md` file owns the merge rules, the baked defaults, and the offer flow; this section covers field naming.

### Always-present fields when customization is accepted

| Field | Type | Purpose |
| --- | --- | --- |
| `activation_steps_prepend` | array of string | Steps that run before standard activation |
| `activation_steps_append` | array of string | Steps that run after greeting, before the first stage |
| `persistent_facts` | array of string | Facts, literal or `file:`-prefixed paths and globs, loaded on activation |
| `on_complete` | string | Hook prompt or command, empty by default |

### Skill-specific scalars, offered only where the matching stage exists

Named by purpose plus a conventional suffix. Scalars follow the last-wins override rule.

| Naming pattern | Use for | Example |
| --- | --- | --- |
| `<purpose>_template` | A file path for a template the skill loads | `brief_template = "assets/brief-template.md"` |
| `<purpose>_output_path` | A writable destination path | `output_path = "{project-root}/docs/briefs"` |
| `run_folder_pattern` | The dated run-folder shape for artifact producers | `run_folder_pattern = "{date}-{slug}"` |
| `on_<event>` | A prompt or command run at a hook point | `on_complete = ""` |

### Standards-not-options arrays, offered only where the stage exists

These arrays append rather than replace, so a team adds to the standard rather than swapping it out. Offer each one only when the skill has a finalize, review, or handoff stage that consumes it.

| Array | Offered when | Entry forms |
| --- | --- | --- |
| `doc_standards` | The skill has a finalize or review stage | `skill:`, `file:`, or plain text |
| `finalize_reviewers` | The skill gates output through reviewers | `skill:` or plain text |
| `external_sources` | The skill pulls in outside context | `file:` or plain text |
| `external_handoffs` | The skill hands off to another stage or tool | `tool:`, `skill:`, or plain text |

## Path resolution inside scalar values

- A bare path like `assets/brief-template.md` resolves from the skill root.
- A `{project-root}/...` path resolves from the project working directory; use it for org-owned overrides.
- Never mix `{project-root}` with a config variable that already contains it, which would double-prefix.

## How SKILL.md reads resolved values

After the resolver step runs, SKILL.md reads a customized value as `{workflow.<name>}`:

```markdown
Load the brief template from `{workflow.brief_template}`.
```

At runtime that resolves to the merged `[workflow].brief_template` scalar, whether the default, a team override, or a personal override. A hardcoded path written beside a declared scalar silently no-ops the override, so SKILL.md must reference the resolved value, never the raw path. The customization scanner flags this.

## Override files

Teams and users override without editing the skill's customize.toml:

- Team: `{project-root}/_bmad/custom/{skill-name}.toml`
- Personal: `{project-root}/_bmad/custom/{skill-name}.user.toml`

Both use the same `[workflow]` block shape. Merge order is the skill's customize.toml, then team, then user.

## Overview section

The Overview is the first section after the title and primes the model for everything that follows. State what the skill does, how it works, and the outcome it delivers.

| Skill type | Shape |
| --- | --- |
| Complex workflow | This skill helps you {outcome} through {approach}. Act as {role}, guiding users through {key stages}. The output is {deliverable}. |
| Simple workflow | This skill {what it does} by {approach}. Act as {role}. Use when {triggers}. Produces {output}. |
| Simple utility | This skill {what it does}. Use when {when to use}. Returns {output format}. |

## Description format

The frontmatter `description` is the primary trigger mechanism; it decides when the model invokes the skill. Most BMad skills are invoked by name, so the description stays conservative to avoid accidental triggering.

The format is two parts, one sentence each: a 5-8 word statement of what the skill does, then a trigger clause naming the phrases the user would actually say.

| Activation style | Trigger clause |
| --- | --- |
| Explicit, the default | `Use when the user requests to 'create a PRD' or 'edit an existing PRD'.` Quoted phrases, conservative, will not fire on a casual mention. |
| Organic or reactive | `Trigger when code imports the anthropic SDK, or the user asks to use the Claude API.` For lightweight skills that activate on contextual signals. |

Good explicit: `Builds workflows and skills through conversational discovery. Use when the user requests to 'build a workflow', 'modify a workflow', or 'quality check workflow'.`

Bad, too vague: `Helps with PRDs and product requirements.` This would fire on any passing mention of a PRD.

Bad, over-broad: `Use on any mention of workflows, building, or creating things.` This would hijack unrelated conversations.

Default to explicit invocation unless the author describes organic activation during discovery.

## Role guidance

Every generated SKILL.md carries a brief role statement in the Overview or as a standalone line:

```markdown
Act as {role}. {brief expertise and approach}.
```

A skill may use a fuller identity and principles section when personality serves the work, but a single role line is enough for most.

## Path rules

### Skill-internal references

Use bare paths from the skill root for any file inside the skill, including a reference between two files in the same folder:

- `references/build-process.md`
- `references/standard-fields.md` referenced from another file in `references/`, still a bare path
- `scripts/validate.py`
- `assets/template.md`

The convention is universal: bare paths from the skill root. Never use a `./` prefix, which causes inconsistency and breaks under context compaction when the working directory shifts.

### Project-scope paths

Use `{project-root}/...` for any path relative to the project root:

- `{project-root}/_bmad/planning/prd.md`
- `{project-root}/docs/report.md`

### Config variables

Use config variables directly, since their resolved values already contain `{project-root}`:

- `{output_folder}/file.md`
- `{planning_artifacts}/prd.md`

### Anti-patterns

These are wrong; the fences keep the path linter from firing on them:

```text
{project-root}/{output_folder}/file.md   # WRONG, double-prefix; the config var already has {project-root}
_bmad/planning/prd.md                    # WRONG, bare _bmad needs a {project-root} prefix
./references/foo.md                       # WRONG, never use ./ for a skill-internal path
./scripts/foo.py                          # WRONG, bare paths from skill root only
```
