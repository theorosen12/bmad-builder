# Complex Workflow Patterns

Patterns for workflows whose SKILL.md grew past what one file can hold and had to carve work out to `references/`. The default for any new skill is inline, where a multi-stage coaching workflow lives in a single SKILL.md. Reach for these patterns only when SKILL.md genuinely will not fit its token budget.

## Carve-Out Conventions

When carving out to `references/`:

- Use descriptive filenames (`press-release.md`, `customer-faq.md`, `verdict.md`), never numbered prefixes. The carve-out is a section, not a step, and SKILL.md decides the order by routing.
- Each file works standalone, because context compaction can drop SKILL.md mid-flow. Do not write "as described in the overview."
- SKILL.md keeps the role paragraph, activation, the conventions block (see `references/skill-quality-principles.md`), and the routing logic. Everything else moves out.
- `assets/` holds templates and other static content the workflow loads, not stages.

## Workflow Persona

BMad workflows treat the human operator as the expert. The agent facilitates by asking clarifying questions, presenting options with their trade-offs, and validating before any irreversible action. The operator knows the domain and the workflow knows the process.

## Config Reading and Integration

Workflows read config from `{project-root}/_bmad/config.yaml` and `config.user.yaml`. Reading project config at activation is not a customization surface, so it stays even in skills that ship fixed. Customization lives only in customize.toml (see `references/customize-toml-guide.md`).

Module-based skills load with fallback and setup-skill awareness:

```
Load config from {project-root}/_bmad/config.yaml ({module-code} section) and config.user.yaml.
If missing: inform user that {module-setup-skill} is available, continue with sensible defaults.
```

Standalone skills load best-effort:

```
Load config from {project-root}/_bmad/config.yaml and config.user.yaml if available.
If missing: continue with defaults, no mention of a setup skill.
```

Config variables resolve already containing `{project-root}`, so never double-prefix.

## Memory: memlog Is the Canonical Process Memory

For workflows that run across turns or produce revisable artifacts, on-disk process memory is the memlog written by `scripts/memlog.py`. The memlog is the load-bearing artifact for identity across sessions. The document is what the user takes away, and the memlog is what carries the decisions, directions, assumptions, gaps, and events that produced it.

The memlog is `.memlog.md`, append-only, written atomically through the CLI. The model captures continuously as decisions and directions land, reads the ack each command prints, and never re-reads the file mid-session. On resume, the parent reads the whole memlog once to rebuild state, then resumes appending.

CLI shape:

| Command | Effect |
|---|---|
| `memlog.py init --path <file>` | Create the memlog |
| `memlog.py append --path <file> --type <type> --text <text>` | Add one typed entry |
| `memlog.py set-complete --path <file>` | Mark the run complete |

Entry types: `decision`, `direction`, `assumption`, `gap`, `note`, `event`. There is no remove or edit command, because history is never rewritten.

For complex workflows that route to carved-out files, each carved file reaches the memlog by its config-resolved path rather than assuming in-context state, because compaction can drop SKILL.md before the carved file runs.

YAML frontmatter on the primary artifact carries status and inputs through a compaction:

```markdown
---
title: 'Analysis: Research Topic'
status: 'discovery'
inputs:
  - '{project-root}/docs/brief.md'
created: '2025-03-02T10:00:00Z'
updated: '2025-03-02T11:30:00Z'
---
```

When not to keep a memlog: purely conversational workflows, one-shot single-turn outputs, and multi-artifact workflows where each artifact gets its own folder and its own memory.

## Three-Mode Architecture

A skill that serves more than one intent routes by mode rather than by branching deep inside a single procedure. The three modes most producing skills land on are create, update, and validate. Each mode has its own entry path, its own resume behavior, and its own memlog interaction, but all three share the role paragraph, activation, and conventions block.

Create starts a fresh run, inits the memlog, and walks discovery through finalize. Update resumes against an existing artifact, reads the memlog once to rebuild state, surfaces any conflict before applying changes, and appends new entries. Validate is read-only, grades the artifact against its standards, and writes nothing the user has to keep.

Mode selection happens at activation from the user's intent, not from a quiz. If the intent is ambiguous, ask the one question that disambiguates, then route. Keep the mode boundary clean so a reader of any single mode never has to reason about the other two.

## Graceful Degradation

A workflow that depends on config, a prior artifact, or an optional script should degrade rather than stop. Each dependency has a named fallback, and the fallback is the path the skill takes when the dependency is absent rather than an error the user has to clear.

| Dependency missing | Degraded behavior |
|---|---|
| Project config.yaml | Continue with sensible defaults; standalone skills say nothing, module skills name the setup skill |
| Prior artifact on update | Offer to start a create run instead |
| Optional non-stdlib script dep | Fall back to the stdlib path and report which path ran |
| customize.toml override files | Resolver reads the three files it can find and uses baked defaults for the rest |

Degradation is a design property, not an exception handler. State the fallback inline where the dependency is read, so the reader sees both the happy path and the floor in one place.

## Multi-Stage Routing as an Earn-It Surface

Multi-stage routing is structure, and structure has to earn its place against a flatter alternative. Before splitting a workflow into routed stages, ask whether a single goal-driven SKILL.md with named sections would have produced the same result. Usually it would, so reach for explicit stages only when the workflow is large enough that SKILL.md cannot hold it within budget, or when stages have genuinely different resume and memory behavior.

When stages earn their place, name them descriptively and route by intent. The stage table near the bottom of SKILL.md is a reading aid that maps an intent to a location:

```markdown
## Stages

| Stage | Intent it serves | Location |
|-------|------------------|----------|
| Ignition | Capture the raw concept, enforce customer-first thinking | SKILL.md (above) |
| Press Release | Iterative drafting with hard coaching | `references/press-release.md` |
| Customer FAQ | Surface devil's-advocate customer questions | `references/customer-faq.md` |
```

The intent routing table is what makes the split worth its cost, because the model reads the user's intent and jumps straight to the stage that serves it rather than walking a fixed sequence. There is no numbered prefix on any stage filename, and the stage order is a routing decision SKILL.md makes per run, not a property baked into the file names.

## Module Metadata Reference

BMad module workflows carry extended frontmatter metadata. See `references/standard-fields.md` for the field conventions. The workflow-builder captures module-capability metadata as handoff fields only and never authors module.yaml.

## Architecture Checklist

Before finalizing a complex BMad workflow:

- [ ] Default reconsidered: would this fit inline as named sections in a single SKILL.md within budget?
- [ ] Facilitator persona treats the operator as the expert
- [ ] Config integration reads language and output locations and uses them
- [ ] Conventions block stamped at the top of SKILL.md when multiple internal files are referenced
- [ ] Carve-outs in `references/` use descriptive names with no numbered prefixes
- [ ] Each carved file works standalone for compaction survival
- [ ] Memory via memlog, with resume reading the file once on activation (or an explicit reason for skipping: simple utility, one-shot, or purely conversational)
- [ ] Three-mode boundary is clean where the skill serves create, update, and validate
- [ ] Each external dependency names its degraded fallback inline
- [ ] Multi-stage routing earned its place against a flat SKILL.md, with an intent routing table
- [ ] Update mode reads the memlog first and surfaces conflicts before applying changes
- [ ] Final polish through a subagent polish step at the end
- [ ] Finalize step distills the run and confirms the memlog is complete
