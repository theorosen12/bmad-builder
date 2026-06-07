# Skill Quality Principles

What earns its place in a BMad skill, and what should be cut. Loaded at build time so the author works to the bar from the start, and at analysis time so every scanner verifies against the same bar. This file is the single source of truth for what "lean" means here.

## The Core Test

For every line you write or review: **would an LLM do this correctly without being told?** If yes, cut it. The instruction must earn its place by preventing a failure that would otherwise happen.

The framing underneath every test in this file is the same one. A line must beat its own absence. If you cannot name something the line produces that its absence would not, the line is friction and it goes. This replaces any older "be effective rather than efficient" idea, because effectiveness and efficiency stop competing once you measure each line against what the skill would do without it.

The reader is the discriminator. Every file in a skill is read by an LLM whose entire context is the skill's own files, so the test is reader-relative and cuts both ways. Cut what that reader already knows and what changes none of its moves — meta-explanation that describes the system to itself, negative-space ("what this no longer does"), restated facts, and downstream mechanics that belong in the file that performs them. But keep the why behind a non-obvious goal: a goal handed over without its reason cannot be generalized to the case you did not foresee, and invites the model to optimize away a constraint it does not understand. A stripped why is under-writing, not leanness. This mirrors the discipline-neutral prompt-quality canon ("Outcome-Driven Prompt Quality" on the docs site).

## What Earns Its Keep

The model already knows how to facilitate, ask questions, write prose, parse intent, and format markdown. Spend file weight on things the bare model would get wrong or would not know:

- **Project paths and outputs**: `{project-root}/...` paths and where the artifact lands.
- **Schema**: frontmatter format, customize.toml shape, downstream contracts.
- **BMad-specific conventions**: naming (`bmad-` prefix, module prefixes), description format, intelligence placement.
- **Hard rules with body count**: the implicit-read trap, subagent-can't-spawn-subagent, compaction survival.
- **Fragile-operation invocations**: exact script commands, exact API calls. One right way.
- **Domain framing and theory-of-mind** for interactive workflows, which is the context that enables judgment.
- **Design rationale** for non-obvious choices, which prevents the LLM from "optimizing" away constraints it doesn't understand.

## What Doesn't Earn Its Keep

- Numbered procedural steps for things the LLM does naturally
- Per-platform adapter files for tools the LLM speaks fluently
- Scoring formulas, weighted calibration tables, decision matrices for subjective judgment
- Templates teaching output formatting, greeting users, or prompt assembly
- "Why It Matters" prose attached to obvious checks
- Defensive padding ("make sure", "don't forget", "remember to")
- Meta-explanation ("This workflow is designed to...")
- Bot personas with rubrics where role plus outcome would do the same job
- Explaining the model to itself ("You are an AI that...")
- Multiple files that could be a single instruction

## Outcome vs Prescriptive

| Prescriptive (avoid) | Outcome-based (prefer) |
| --- | --- |
| "Step 1: Ask about goals. Step 2: Ask about constraints. Step 3: Summarize and confirm." | "Ensure the user's vision is fully captured (goals, constraints, and edge cases) before proceeding." |
| "Read the file. Extract the title. Extract each heading. List them in order." | "Summarize the document's structure." |
| "Create a file. Write the header. Write section 1. Write section 2. Save." | "Produce a report covering X, Y, and Z." |

The prescriptive versions miss requirements the author didn't think of. The outcome-based versions let the LLM adapt to the input in front of it.

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

The order test for any numbered sequence: would a different order change the outcome? If no step depends on a prior step's output, the numbering is decoration and the sequence should collapse to one goal sentence. Numbering stays only where the order guards against a named failure.

## BMad Institutional Knowledge

Things the bare model genuinely won't know. This is what your file weight buys.

### Naming
- Skill name = folder name (kebab-case)
- Module skill: `{module-code}-{name}` (e.g. `bmm-create-prd`, `cis-brainstorm`)
- Standalone: `{name}`
- The `bmad-` prefix is reserved for official BMad creations

### Description format
Two parts: `[5-8 word summary]. [Use when user says 'specific phrase' or 'specific phrase'.]`

Quote the trigger phrases. Default to conservative (explicit) triggering, since most BMad skills are explicitly invoked. Organic triggering is reserved for skills that should activate on context (e.g. "Trigger when code imports the anthropic SDK").

Bad: `Helps with PRDs and product requirements.` It is too vague and will hijack unrelated conversations.

### Path conventions
All file references in a skill use bare paths from the skill root. The canonical Resolution rules block, stamped into any SKILL.md that references multiple internal files:

```
## Resolution rules
- Bare paths and `{skill-root}` (e.g. `references/press-release.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `{skill-name}` → the skill directory's basename.
```

Additional rules:
- Forward slashes only (cross-platform).
- Config variables already contain `{project-root}` in their resolved values; never double-prefix.
- `references/` is for prompt content carved out of SKILL.md. `assets/` is for templates and other static content the workflow loads. `scripts/` is for deterministic code. Never put workflow content directly at skill root.

### Customization (customize.toml)
The full spec — fields, defaults, merge rules, and offer flow — lives in `references/customize-toml-guide.md`. The rules the scanner checks against:

Always-present fields: `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` (each an array; overrides append).

Workflow-specific scalars, lifted only during configurability discovery:
- `<purpose>_template` for template file paths
- `<purpose>_output_path` for writable destinations
- `on_<event>` for hook scalars

Arrays of tables MUST key on `code` or `id` (the resolver merges by key; without it, it falls back to append-only).

Merge rules: scalars override, tables deep-merge, arrays-of-tables key-merge, plain arrays append.

Override files: `{project-root}/_bmad/custom/{skill-name}.toml` (team), `.user.toml` (personal). Merge order: base then team then user.

SKILL.md must reference resolved values as `{workflow.<name>}`. A hardcoded path next to a declared scalar silently no-ops the override.

### Customize.toml surface economics
The surface is a cost, not a feature. Every offered point is a permutation the author now owns and a thing a scanner has to reason about. Two failure shapes bracket the right size.

Too thin starves real reuse: a skill that bakes a path or a template it should have exposed forces anyone who needs a variation to fork the whole skill. Too loud is worse: a boolean toggle, an options menu, or an identity block in `[workflow]` means the author never decided what the skill does and pushed that decision onto every installer, turning the surface into a permutation forest nobody can test. The right surface exposes only the points whose stages actually exist in this skill, names a real default for each, and lets the rare divergent case fork.

customize.toml is the only customization mechanism. There is no installer question, no module.yaml embedding, and no settings concept inside a built skill. Net-new skills are not taught to read `config.yaml`; customize.toml plus baked defaults is the surface, and a user who wants project-config wiring can add it. Confirming script dependencies at build is not a customization surface and stays.

### Intelligence placement
The boundary between what a script does and what a prompt does is sharp, and crossing it in either direction is a defect.

- Scripts handle plumbing: fetch, parse, validate, count, transform.
- Prompts handle judgment: interpret, classify, decide.
- A script using regex to decide what content MEANS is an intelligence leak into the script.
- A prompt validating structure, counting items, or comparing against a schema is a determinism leak into the LLM.

When you catch a determinism leak, that is a script opportunity; route it to the script-opportunities reference for the determinism test and the signal-verb scan.

### Workflows: inline first, carve out only when needed
Default: write the entire workflow as named sections in SKILL.md (`## Discovery`, `## Constraints`, `## Finalize`, and so on). A multi-stage coaching workflow can live in one SKILL.md.

Carve out to `references/` only when SKILL.md genuinely gets too big to scan. When you do:
- **Descriptive filenames preferred.** `references/press-release.md`, `references/customer-faq.md` over `01-press-release.md`; the carve-out is a section, not a "step," and SKILL.md routes by name. Numbered prefixes are allowed, just not the default.
- Each carved-out file works standalone, since context compaction can drop SKILL.md mid-flow. No "as described in the overview."
- Progression conditions, where they exist, must be testable ("when X is captured, route to Y"). "When ready" is vague.
- The file uses `{communication_language}` (and `{document_output_language}` if it produces a doc).
- There are NO exit hooks in the system. Don't add `## On Exit` sections, because they would never run.

### Headless mode

When a skill supports headless invocation, the memlog absorbs every assumption made without the user: intent inference, proposed names, customization defaults, conflict resolutions, lint-fix calls, anything the user would have weighed in on interactively. Append these as typed `assumption` and `decision` entries through `scripts/memlog.py` as they happen. The JSON return is the smallest set of paths the caller needs (typically `skill` plus the memlog path, plus the report path for analysis flows); the memlog carries the reasoning. `status` is `complete` or `blocked`; on `blocked`, include a one-line `reason` and still return the memlog path so the caller can read the detail. Without this discipline, headless silently buries its calls and the audit trail breaks on the next session.

### Subagent constraints
- Subagents CANNOT spawn other subagents. Chain through the parent.
- Don't read files in the parent if you can delegate the read; the parent stays lean.
- Subagent prompts must specify the exact return format and an "ONLY return X" constraint, or you get verbose prose back.
- **The implicit-read trap:** language like "review", "acknowledge", or "summarize what you have" causes the parent to read files even when you didn't ask for it. If a later stage delegates document analysis, earlier stages must NOT use that language. Use "note paths for subagent scanning; don't read them now".

### Length guidance
Length is measured in tiktoken tokens through `scripts/count_tokens.py` (`cl100k_base`, with a chars/4 fallback when tiktoken is unavailable). There is no line-count gate anywhere. The "what fails if I delete this?" test still applies to every line; budgets are a guardrail, not the goal.

SKILL.md is tiered against two org-configurable thresholds, `{workflow.skill_md_token_desired}` (default 1200) and `{workflow.skill_md_token_budget}` (default 2000):

- **Under desired** — on target; no action.
- **Between desired and budget** — warn the user that SKILL.md is getting heavy and name the section most worth lifting, but do not block.
- **Over budget** — a hard finding. Bring it back under budget through progressive disclosure: lift the largest self-contained section to `references/` or `assets/` and leave a one-line pointer, rather than compressing prose into something the model has to decode. Repeat until under `{workflow.skill_md_token_budget}`.

| File kind | Token budget |
| --- | --- |
| SKILL.md | `{workflow.skill_md_token_desired}` aim / `{workflow.skill_md_token_budget}` hard |
| Multi-branch reference | ~4500 |
| Single-purpose reference | ~9000 |

When any reference file runs past its budget, lift a section the same way.

### Patterns BMad has seen pay off
Institutional names for patterns the LLM won't generate by default:

- **Open-floor opening**: Conversational skills start with an explicit invitation for the user to share everything they have (goals, references, examples, paths to artifacts) before any structured Q&A. The dump replaces most of the question script that would otherwise follow, and the agent then asks only what's missing. The form adapts to the input: a vague request gets "tell me everything", a path or URL gets "what do you want focused on?". It costs almost nothing token-wise and drastically improves the conversational feel.
- **Soft-gate elicitation**: "Anything else, or shall we move on?" at natural transitions. Users always remember one more thing when given a graceful exit.
- **Intent-before-ingestion**: Understand why the user is here before scanning artifacts, because without intent the scanning is noise.
- **Capture-don't-interrupt**: Out-of-scope insights mid-flow get captured silently rather than redirected. Users in flow share their best material unprompted.
- **Dual-output**: Human artifact plus an LLM distillate, when the artifact will feed downstream agents.
- **Parallel review lenses**: Fan out two or three review subagents (skeptic, opportunity-spotter, a contextually-chosen lens) before finalizing a significant artifact.
- **Three-mode architecture**: Guided, Yolo, Headless. Not every skill needs all three, but considering it during design prevents lock-in.
- **Graceful degradation**: Subagent-dependent features fall back to sequential when subagents are unavailable.
- **Working state across turns**: a multi-turn skill that builds something holds state as a memlog (the decision trail), a structured working artifact (the work-in-progress that transforms into the output), both, or neither. The choice and the full treatment live in `references/working-state-patterns.md`.

### Writing
- One term per concept; pick it and stick to it.
- Third person in descriptions ("Processes files", not "I help process files").
- Descriptive file names (`form-validation-rules.md`, not `doc2.md`).
- One level deep for reference files: SKILL.md to a reference, never SKILL to ref to ref.

## Failure Modes With Body Count

- **Description over-broadens** → Skill hijacks unrelated conversations. Fix: quote trigger phrases.
- **Vague progression conditions** ("when ready") → Stage never advances or advances early. Fix: testable conditions.
- **Stage references SKILL.md** ("as above") → Breaks on compaction. Fix: make stages self-contained.
- **Subagent prompt without explicit return format** → Verbose prose responses. Fix: "Return ONLY {schema}. No other output."
- **Parent reads then delegates analysis** → Context bloat that makes the delegation pointless. Fix: delegate the read.
- **Implicit-read trap** in a stage that precedes subagent delegation → Parent reads everything anyway. Fix: explicit "don't read these now".
- **Scoring formulas for subjective judgment** → Rigidity that doesn't improve quality. Fix: state the outcome, let the model assess.
- **Boolean toggles in customize.toml** → Author didn't decide what the skill does; the surface becomes a permutation forest. Fix: pick a default and let users fork if they want the other shape.
- **Hardcoded path in SKILL.md while customize.toml declares the scalar** → Override silently does nothing. Fix: SKILL.md must read `{workflow.<name>}`.
- **Identity, communication style, or principles in `[workflow]`** → The workflow wants to be an agent. Fix: point the author at agent-builder and remove it from the workflow surface.
- **Numbered sequence whose order doesn't matter** → Decoration that reads as a real constraint and resists cutting. Fix: collapse to one goal sentence.
- **ALL-CAPS ALWAYS/NEVER and stacked MUSTs** → Yellow flag that the author is shouting instead of explaining. Fix: reframe as the reasoning the rule protects.
- **Multi-turn producing skill with no working-state strategy** → state lives only in the conversation and dies on compaction or revisit. Fix: choose a memlog or a structured working artifact (`references/working-state-patterns.md`).
- **Working-state strategy buried under ceremony** → a memlog-discipline enumeration or a meta `## Workspace` section pays the pattern's cost without its value. Fix: thread it through the intents at the points that matter; `bmad-product-brief` is the model.
