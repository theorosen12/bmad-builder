# Complex Workflow Patterns

Patterns for workflows whose SKILL.md grew past what one file can hold and had to carve work out to `references/`. The default for any new skill is inline, where a multi-stage coaching workflow lives in a single SKILL.md. Reach for these patterns only when SKILL.md genuinely will not fit its token budget.

The portable patterns most producing skills need — persona, intent modes, graceful degradation, and memory — live in `references/producing-workflow-patterns.md`; this file is only the carve-out and routing mechanics.

## Carve-Out Conventions

When carving out to `references/`:

- Prefer descriptive filenames (`press-release.md`, `customer-faq.md`, `verdict.md`) over numbered prefixes. The carve-out is a section, not a step, and SKILL.md decides the order by routing.
- Each file works standalone, because context compaction can drop SKILL.md mid-flow. Do not write "as described in the overview."
- SKILL.md keeps the role paragraph, activation, the resolution rules block (see `references/skill-quality-principles.md`), and the routing logic. Everything else moves out.
- `assets/` holds templates and other static content the workflow loads, not stages.
- Carved files reach the memlog by their resolved path rather than assuming in-context state, because compaction can drop SKILL.md before the carved file runs.

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

The intent routing table is what makes the split worth its cost, because the model reads the user's intent and jumps straight to the stage that serves it rather than walking a fixed sequence. Stage order is a routing decision SKILL.md makes per run rather than something baked into the file names, which is why descriptive names are preferred over numbered prefixes.

## Module Metadata Reference

BMad module workflows carry extended frontmatter metadata. See `references/standard-fields.md` for the field conventions. The workflow-builder captures module-capability metadata as handoff fields only and never authors module.yaml.

## Carve-Out Checklist

Before finalizing a carved-out workflow (in addition to the producing-skill checklist):

- [ ] Default reconsidered: would this fit inline as named sections in a single SKILL.md within budget?
- [ ] Resolution rules block stamped at the top of SKILL.md when multiple internal files are referenced
- [ ] Carve-outs in `references/` prefer descriptive names over numbered prefixes
- [ ] Each carved file works standalone for compaction survival
- [ ] Multi-stage routing earned its place against a flat SKILL.md, with an intent routing table
