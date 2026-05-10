# Skill Quality Principles

What earns its place in a BMad skill, and what should be cut. Loaded at both build time (so the author follows the bar upfront) and at quality-analysis time (so scanners verify against the same bar).

## The Core Test

For every line you write or review: **would an LLM do this correctly without being told?** If yes, cut it. The instruction must earn its place by preventing a failure that would otherwise happen.

## What Earns Its Keep

The model already knows how to facilitate, ask questions, write prose, parse intent, and format markdown. Spend file weight on:

- **Project paths and outputs** — `{project-root}/...`, config-resolved paths, where the artifact lands.
- **Schema** — frontmatter format, customize.toml shape, downstream contracts.
- **BMad-specific conventions** — naming (`bmad-` prefix, module prefixes), description format, intelligence placement.
- **Hard rules with body count** — the implicit-read trap, subagent-can't-spawn-subagent, compaction survival.
- **Fragile-operation invocations** — exact script commands, exact API calls. One right way.
- **Domain framing and theory-of-mind** for interactive workflows — context that enables judgment.
- **Design rationale** for non-obvious choices — prevents the LLM from "optimizing" away constraints it doesn't understand.

## What Doesn't Earn Its Keep

- Numbered procedural steps for things the LLM does naturally
- Per-platform adapter files for tools the LLM speaks fluently
- Scoring formulas, weighted calibration tables, decision matrices for subjective judgment
- Templates teaching output formatting, greeting users, or prompt assembly
- "Why It Matters" prose attached to obvious checks
- Defensive padding ("make sure", "don't forget", "remember to")
- Meta-explanation ("This workflow is designed to...")
- Bot personas with rubrics where role + outcome would do the same job
- Explaining the model to itself ("You are an AI that...")
- Multiple files that could be a single instruction

## Outcome vs Prescriptive

| Prescriptive (avoid) | Outcome-based (prefer) |
| --- | --- |
| "Step 1: Ask about goals. Step 2: Ask about constraints. Step 3: Summarize and confirm." | "Ensure the user's vision is fully captured — goals, constraints, and edge cases — before proceeding." |
| "Load config. Read user_name. Read communication_language. Greet by name in their language." | "Load available config and greet the user appropriately." |
| "Create a file. Write the header. Write section 1. Write section 2. Save." | "Produce a report covering X, Y, and Z." |

The prescriptive versions miss requirements the author didn't think of. The outcome-based versions let the LLM adapt.

## When Procedure IS Value

Reserve exact steps for fragile operations where deviation has consequences:

- Exact script invocations (`python3 scripts/foo.py {arg}`)
- Specific file paths and config keys
- API calls with precise parameters
- Security-critical operations
- The customize.toml resolver step

| Freedom | When | Example |
| --- | --- | --- |
| **High** (outcomes) | Multiple valid approaches, LLM judgment adds value | "Ensure the user's requirements are complete" |
| **Medium** (guided) | Preferred approach exists, some variation OK | "Present findings in a structured report with an executive summary" |
| **Low** (exact) | Fragile, one right way, consequences for deviation | `python3 scripts/scan-path-standards.py {skill-path}` |

## BMad Institutional Knowledge

Things the bare model genuinely won't know. This is what your file weight buys.

### Naming
- Skill name = folder name (kebab-case)
- Module skill: `{module-code}-{name}` (e.g. `bmm-create-prd`, `cis-brainstorm`)
- Standalone: `{name}`
- The `bmad-` prefix is reserved for official BMad creations

### Description format
Two parts: `[5-8 word summary]. [Use when user says 'specific phrase' or 'specific phrase'.]`

Quote the trigger phrases. Default to conservative (explicit) triggering — most BMad skills are explicitly invoked. Organic triggering is reserved for skills that should activate on context (e.g. "Trigger when code imports anthropic SDK").

Bad: `Helps with PRDs and product requirements.` (too vague — hijacks unrelated conversations).

### Path conventions
All file references in a skill use bare paths from the skill root. The canonical Conventions block (from `bmad-prfaq/SKILL.md`) — stamp it into any SKILL.md that references multiple internal files:

```
## Conventions
- Bare paths (e.g. `references/press-release.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.
```

Additional rules:
- Forward slashes only (cross-platform).
- Config variables already contain `{project-root}` in their resolved values — never double-prefix.
- `references/` is for prompt content carved out of SKILL.md. `assets/` is for templates and other static content the workflow loads. `scripts/` is for deterministic code. Never put workflow content directly at skill root.

### Customization (customize.toml)
Always-present fields: `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` (each is an array; overrides append).

Workflow-specific scalars (lifted during configurability discovery):
- `<purpose>_template` for template file paths
- `<purpose>_output_path` for writable destinations
- `on_<event>` for hook scalars

Arrays of tables MUST key on `code` or `id` (resolver merges by key; without it, falls back to append-only).

Merge rules: scalars override, tables deep-merge, arrays-of-tables key-merge, plain arrays append.

Override files: `{project-root}/_bmad/custom/{skill-name}.toml` (team), `.user.toml` (personal). Merge order: base → team → user.

Default `persistent_facts`: `["file:{project-root}/**/project-context.md"]` is BMad's convention.

SKILL.md must reference resolved values as `{workflow.<name>}`. Hardcoded paths next to a declared scalar = override silently no-ops.

### Intelligence placement
- Scripts handle plumbing: fetch, parse, validate, count, transform.
- Prompts handle judgment: interpret, classify, decide.
- Script using regex to decide what content MEANS = intelligence leak into the script.
- Prompt validating structure, counting items, comparing against schemas = determinism leak into the LLM.

### Workflows: inline first, carve out only when needed
Default: write the entire workflow as named sections in SKILL.md (`## Discovery`, `## Constraints`, `## Finalize`, etc.). `bmad-product-brief` is the canonical model — a multi-stage coaching workflow that lives in one SKILL.md.

Carve out to `references/` only when SKILL.md genuinely gets too big to scan. When you do:
- **Descriptive filenames.** `references/press-release.md`, `references/customer-faq.md`. Never numbered prefixes (`01-press-release.md`) — the carve-out is a section, not a "step." SKILL.md routes to references by name and the order is whatever SKILL.md specifies.
- Each carved-out file works standalone — context compaction can drop SKILL.md mid-flow. No "as described in the overview."
- Progression conditions, where they exist, must be testable ("when X is captured, route to Y"). "When ready" is vague.
- The file uses `{communication_language}` (and `{document_output_language}` if it produces a doc).
- There are NO exit hooks in the system. Don't add `## On Exit` sections — they'd never run.

### Subagent constraints
- Subagents CANNOT spawn other subagents. Chain through parent.
- Don't read files in parent if you can delegate the read — parent stays lean.
- Subagent prompts must specify exact return format and "ONLY return X" constraint, or you get verbose prose.
- **The implicit-read trap:** Language like "review", "acknowledge", "summarize what you have" causes the parent to read files even when you didn't ask for it. If a later stage delegates document analysis, earlier stages must NOT use that language. Use "note paths for subagent scanning; don't read them now".

### Size guidance
Production targets, not hard limits. The "what fails if I delete this?" test still applies to every line.

- SKILL.md: ~80 lines target, hard ceiling ~130
- Multi-branch SKILL.md: up to ~250 lines if each branch has brief contextual explanation
- Single-purpose: up to ~500 lines (~5000 tokens) if focused
- Past those: lift to `references/` or `assets/`

### Patterns BMad has seen pay off
Institutional names for patterns the LLM won't generate by default:

- **Soft-gate elicitation** — "Anything else, or shall we move on?" at natural transitions. Users always remember one more thing when given a graceful exit.
- **Intent-before-ingestion** — Understand why the user is here before scanning artifacts. Without intent, scanning is noise.
- **Capture-don't-interrupt** — Out-of-scope insights mid-flow get captured silently, not redirected. Users in flow share their best stuff unprompted.
- **Dual-output** — Human artifact + LLM distillate, when the artifact will feed downstream agents.
- **Parallel review lenses** — Fan out 2-3 review subagents (skeptic, opportunity-spotter, contextually-chosen lens) before finalizing significant artifacts.
- **Three-mode architecture** — Guided / Yolo / Headless. Not all skills need all three; considering it during design prevents lock-in.
- **Graceful degradation** — Subagent-dependent features fall back to sequential when subagents are unavailable.
- **Document-as-cache** — Long-running workflows write progressively to the output doc with YAML front matter (status + inputs). Surviving compaction = re-reading the doc.

### Writing
- One term per concept; pick it and stick to it.
- Third person in descriptions ("Processes files", not "I help process files").
- Descriptive file names (`form-validation-rules.md`, not `doc2.md`).
- One level deep for reference files — SKILL.md → reference, never SKILL → ref → ref chains.

## Failure Modes With Body Count

- **Description over-broadens** → Skill hijacks unrelated conversations. Fix: quote trigger phrases.
- **Vague progression conditions** ("when ready") → Stage never advances or advances early. Fix: testable conditions.
- **Stage references SKILL.md** ("as above") → Breaks on compaction. Fix: stages self-contained.
- **Subagent prompt without explicit return format** → Verbose prose responses. Fix: "Return ONLY {schema}. No other output."
- **Parent reads then delegates analysis** → Context bloat that makes delegation pointless. Fix: delegate the read.
- **Implicit-read trap** in a stage that precedes subagent delegation → Parent reads everything anyway. Fix: explicit "don't read these now".
- **Scoring formulas for subjective judgment** → Rigidity that doesn't improve quality. Fix: state the outcome, let the model assess.
- **Boolean toggles in customize.toml** → Author didn't decide what the skill does; surface becomes a permutation forest. Fix: pick a default; users fork if they want the other shape.
- **Hardcoded path in SKILL.md while customize.toml declares the scalar** → Override silently does nothing. Fix: SKILL.md must read `{workflow.<name>}`.
- **Identity / communication-style / principles in `[workflow]`** → Workflow wants to be an agent. Fix: point author at agent-builder; remove from workflow surface.
