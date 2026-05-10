# Complex Workflow Patterns

Patterns for workflows whose SKILL.md got too big and had to carve out to `references/`. The default for any new skill is **inline** — `bmad-product-brief` is the canonical model, a multi-stage coaching workflow that lives in a single SKILL.md. Reach for these patterns only when SKILL.md genuinely won't fit.

## Carve-Out Conventions

When carving out to `references/`:

- Descriptive filenames (`press-release.md`, `customer-faq.md`, `verdict.md`). Never numbered prefixes — the carve-out is a section, not a "step." SKILL.md decides the order by routing.
- Each file works standalone (context compaction can drop SKILL.md). No "as described in the overview."
- SKILL.md keeps Overview, Activation, the Conventions block (see `./skill-quality-principles.md`), and the routing logic. Everything else moves out.
- `assets/` is for templates and other static content the workflow loads, not for stages.

## Workflow Persona

BMad workflows treat the human operator as the expert. The agent facilitates — asks clarifying questions, presents options with trade-offs, validates before irreversible actions. The operator knows their domain; the workflow knows the process.

## Config Reading and Integration

Workflows read config from `{project-root}/_bmad/config.yaml` and `config.user.yaml`.

**Module-based skills** load with fallback and setup-skill awareness:

```
Load config from {project-root}/_bmad/config.yaml ({module-code} section) and config.user.yaml.
If missing: inform user that {module-setup-skill} is available, continue with sensible defaults.
```

**Standalone skills** load best-effort:

```
Load config from {project-root}/_bmad/config.yaml and config.user.yaml if available.
If missing: continue with defaults — no mention of a setup skill.
```

Config variables resolved already contain `{project-root}` — never double-prefix.

## Long-Running Workflows: Compaction Survival

Workflows that run long may trigger context compaction. Critical state must survive in output files.

**The Document-Itself Pattern.** The output document is the cache. Write directly to the file you're creating, updating progressively. The document stores both content and context:

- YAML frontmatter — paths to input files, current status, current phase
- Draft sections — progressive content as it's built
- Status marker — which phase is complete

After the first phase, each subsequent phase reads the output document to recover context. If compacted, re-read input files listed in the YAML frontmatter.

```markdown
---
title: 'Analysis: Research Topic'
status: 'analysis'
inputs:
  - '{project-root}/docs/brief.md'
created: '2025-03-02T10:00:00Z'
updated: '2025-03-02T11:30:00Z'
---
```

**Use when:** Guided flows with long documents, yolo flows with multiple turns. **Don't use when:** Short single-turn outputs, purely conversational workflows, multiple independent artifacts (each gets its own file).

## Routing from SKILL.md

When SKILL.md routes to a carved-out file, the route is by descriptive name. Use a Stages table near the bottom of SKILL.md:

```markdown
## Stages

| # | Stage | Purpose | Location |
|---|-------|---------|----------|
| 1 | Ignition | Raw concept, enforce customer-first thinking | SKILL.md (above) |
| 2 | Press Release | Iterative drafting with hard coaching | `references/press-release.md` |
| 3 | Customer FAQ | Devil's advocate customer questions | `references/customer-faq.md` |
```

The `#` is a reading aid for the table, not a filename prefix.

## Module Metadata Reference

BMad module workflows require extended frontmatter metadata. See `references/metadata-reference.md` for the metadata template and field explanations.

## Architecture Checklist

Before finalizing a complex BMad workflow:

- [ ] Default reconsidered — would this fit inline as named sections in a single SKILL.md?
- [ ] Facilitator persona — treats the operator as expert?
- [ ] Config integration — language, output locations read and used?
- [ ] Conventions block stamped at top of SKILL.md (when multiple internal files are referenced)
- [ ] Carve-outs in `references/` use descriptive names, no numbered prefixes
- [ ] Each carved file works standalone (compaction survival)
- [ ] Document-as-cache — YAML frontmatter with status and inputs (for long flows)
- [ ] Final polish — subagent polish step at the end?
- [ ] Recovery — can resume by reading output doc frontmatter?
