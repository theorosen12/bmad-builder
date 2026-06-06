# Skill Quality Principles

What earns its place in a BMad skill, and what should be cut. Loaded at build time so the author works to the bar from the start, and at analysis time so every scanner verifies against the same bar. This file is the single source of truth for what "lean" means here.

## The Core Test

For every line you write or review: **would an LLM do this correctly without being told?** If yes, cut it. The instruction must earn its place by preventing a failure that would otherwise happen.

The framing underneath every test in this file is the same one. A line must beat its own absence. If you cannot name something the line produces that its absence would not, the line is friction and it goes. This replaces any older "be effective rather than efficient" idea, because effectiveness and efficiency stop competing once you measure each line against what the skill would do without it.

## What Earns Its Keep

The model already knows how to facilitate, ask questions, write prose, parse intent, and format markdown. Spend file weight on things the bare model would get wrong or would not know:

- **Project paths and outputs**: `{project-root}/...`, config-resolved paths, where the artifact lands.
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
| "Load config. Read user_name. Read communication_language. Greet by name in their language." | "Load available config and greet the user appropriately." |
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
All file references in a skill use bare paths from the skill root. The canonical Conventions block (from `bmad-prfaq/SKILL.md`), stamped into any SKILL.md that references multiple internal files:

```
## Conventions
- Bare paths (e.g. `references/press-release.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.
```

Additional rules:
- Forward slashes only (cross-platform).
- Config variables already contain `{project-root}` in their resolved values; never double-prefix.
- `references/` is for prompt content carved out of SKILL.md. `assets/` is for templates and other static content the workflow loads. `scripts/` is for deterministic code. Never put workflow content directly at skill root.

### Customization (customize.toml)
Always-present fields: `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` (each an array; overrides append).

Workflow-specific scalars, lifted only during configurability discovery:
- `<purpose>_template` for template file paths
- `<purpose>_output_path` for writable destinations
- `on_<event>` for hook scalars

Arrays of tables MUST key on `code` or `id` (the resolver merges by key; without it, it falls back to append-only).

Merge rules: scalars override, tables deep-merge, arrays-of-tables key-merge, plain arrays append.

Override files: `{project-root}/_bmad/custom/{skill-name}.toml` (team), `.user.toml` (personal). Merge order: base then team then user.

Default `persistent_facts`: `["file:{project-root}/**/project-context.md"]` is BMad's convention.

SKILL.md must reference resolved values as `{workflow.<name>}`. A hardcoded path next to a declared scalar silently no-ops the override.

### Customize.toml surface economics
The surface is a cost, not a feature. Every offered point is a permutation the author now owns and a thing a scanner has to reason about. Two failure shapes bracket the right size.

Too thin starves real reuse: a skill that bakes a path or a template it should have exposed forces anyone who needs a variation to fork the whole skill. Too loud is worse: a boolean toggle, an options menu, or an identity block in `[workflow]` means the author never decided what the skill does and pushed that decision onto every installer, turning the surface into a permutation forest nobody can test. The right surface exposes only the points whose stages actually exist in this skill, names a real default for each, and lets the rare divergent case fork.

customize.toml is the only customization mechanism. There is no installer question, no module.yaml embedding, no separate config.yaml authoring, and no settings concept inside a built skill. Reading project config at activation and confirming script dependencies at build are not customization surfaces and stay.

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
- **Descriptive filenames.** `references/press-release.md`, `references/customer-faq.md`. Never numbered prefixes (`01-press-release.md`), because the carve-out is a section, not a "step." SKILL.md routes to references by name and the order is whatever SKILL.md specifies.
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

| File kind | Token budget |
| --- | --- |
| SKILL.md | ~1500-2500 |
| Multi-branch reference | ~4500 |
| Single-purpose reference | ~9000 |

When a file runs past its budget, lift a section to `references/` or `assets/` rather than compressing the prose into something the model has to decode.

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
- **memlog as process memory**: multi-turn workflows that produce a revisable artifact keep a typed append-only log as canonical memory. See the full treatment below.

### Writing
- One term per concept; pick it and stick to it.
- Third person in descriptions ("Processes files", not "I help process files").
- Descriptive file names (`form-validation-rules.md`, not `doc2.md`).
- One level deep for reference files: SKILL.md to a reference, never SKILL to ref to ref.

## The memlog Pattern

The default for any multi-turn workflow that produces a substantive artifact, may be revisited (Update or Validate), or risks running long enough to compact.

**Core insight.** The memlog is the load-bearing record, not the document. The document is what the user takes; the memlog is what carries identity across sessions, prevents the agent from railroading the user, surfaces conflicts on update, and creates an audit trail when the user overrides their own past calls. Workflows that lack it look fine on the first pass and fall apart on revisit.

The memlog is typed, append-only, and written through `scripts/memlog.py` to a `.memlog.md` file beside the primary artifact. The model never edits or re-reads it mid-session; it appends one typed entry at a time and trusts the one-line JSON ack the script returns. The cycle is capture (append as decisions and directions land), distill (at finalize, account for every entry), and project (read the whole log once on resume or when building a summary).

### Entry types and the CLI

The script exposes three subcommands and one set of entry types:

- `init --path <file>` creates the log.
- `append --path <file> --type <type> --text <text>` adds one typed entry; `<type>` is one of `decision`, `direction`, `assumption`, `gap`, `note`, `event`.
- `set-complete --path <file>` marks the workflow done.

Each command prints a one-line JSON ack (`{"ok": true, ...}`). The write is atomic (temp file, fsync, rename) so an interrupted run never half-writes an entry, and there is no edit or remove subcommand by design, because history is never rewritten.

### Workspace layout

Files live in a single folder rooted at the primary artifact. When the artifact is a single document, the workspace is the document's containing folder and the log sits as a peer. When the artifact is itself a folder (a built skill, a generated module), the workspace IS that folder and `.memlog.md` sits beside the primary file such as `SKILL.md`. Either way the workspace exists from the moment intent is confirmed, so the user knows the path immediately and state lives on disk rather than in the conversation.

An optional `distillate.md` holds a token-efficient version of the primary for downstream LLM consumers, created only when the artifact will feed other agents.

### Resume protocol

On activation, check whether a `.memlog.md` already exists for this artifact (glob for `.memlog.md`, never `.decision-log.md`). If found, surface it, read it once to rebuild state, and offer to resume. The single read recovers full context regardless of compaction; after that the workflow resumes append-only.

### Update mode

Read the memlog first. The change request enters as a change signal against the standing record. If the change contradicts a prior decision, surface the conflict before applying it. Every change, clean or override, gets a new `decision` entry, and an override also records the rejected reasoning so it lives somewhere.

### Validate mode

Read the memlog first. A validation that ignores prior decisions or stated user criteria is shallow; it should challenge the artifact against the standards the user themselves set, not against a generic rubric.

### Finalize step

Distill the memlog. Every meaningful entry must be either captured in the primary artifact or explicitly set aside as process noise, and then call `set-complete`. The user ends the session with a shared accounting of how their thinking was handled rather than a one-sided polish-and-deliver.

### When NOT to use

- Simple utilities, where there are no decisions to log and the input/output is the contract.
- One-shot code operations, where the diff is the record.
- Purely conversational skills, where no artifact persists.

### Treatment style (writing it into a skill)

State the principle once where it first applies, typically inside the Create intent as a single clause ("write the primary skeleton and init `.memlog.md` in the workspace; the memlog is canonical process memory"). Mention reads at the moments that matter: Update reads the log before changing decisions, Validate reads it before critiquing, Finalize distills it at handoff. That is the entire treatment.

Do NOT:
- Open with a "memlog discipline" enumeration of what to log; the LLM knows, so trust it.
- Write a separate `## Workspace` section with a meta-explanation of the pattern.
- Include a tree diagram of the layout, because the workspace is just files the LLM names as it uses them.
- Split workspace creation into separate "for new" and "for existing" sub-sections, since "init if absent, append if present" is one sentence.

The scanner flags skills that bury memlog guidance under ceremony. `bmad-product-brief` is the canonical example: about five sentences total, threaded through Create, Update, Validate, Constraints, and Finalize at the points where each matters.

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
