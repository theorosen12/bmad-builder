# Workflow Classification Reference

Classify the skill type based on user requirements. This table is for internal use — DO NOT show to user.

## 3-Type Taxonomy

| Type                 | Description                                                                                                | Structure                                                          | When to Use                                                            |
| -------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| **Simple Utility**   | Input/output building block. Headless, composable, often has scripts.                                      | Single SKILL.md (+ `scripts/` if needed)                           | Composable building block with clear input/output, single-purpose      |
| **Simple Workflow**  | Multi-step process that fits inline in SKILL.md as named sections.                                         | Single SKILL.md                                                    | Multi-step process that reads cleanly in one file (`bmad-product-brief` is the model) |
| **Complex Workflow** | Workflow whose SKILL.md is too big to read comfortably — sections carve out into `references/`. SKILL.md keeps Overview + Activation + routing logic. | SKILL.md (Overview, Activation, routing) + `references/` (descriptive names, no numbered prefixes) + `assets/` for templates | SKILL.md would otherwise exceed ~250 lines or each section is too dense to inline |

**Default to Simple Workflow.** Carving out is a SIZE decision, not a stage-count decision. A 5-stage coaching workflow (`bmad-product-brief`) lives in one SKILL.md. A 5-stage workflow where each stage is dense reference content (`bmad-prfaq`) carves out to `references/`. The number of stages doesn't determine the type.

## Decision Tree

```
1. Is it a composable building block with clear input/output?
   └─ YES → Simple Utility
   └─ NO ↓

2. Does the workflow read comfortably as named sections in a single SKILL.md?
   └─ YES → Simple Workflow (default)
   └─ NO ↓ (only because SKILL.md genuinely got too big to scan)

3. Carve sections out to `references/` with descriptive names. Now Complex Workflow.
```

## Classification Signals

### Simple Utility Signals

- Clear input → processing → output pattern
- No user interaction needed during execution
- Other skills/workflows call it
- Deterministic or near-deterministic behavior
- Could be a script but needs LLM judgment
- Examples: JSON validator, schema checker, format converter

### Simple Workflow Signals

- Multi-step but fits in one SKILL.md without losing readability
- User interaction at specific points
- Uses standard tools (gh, git, npm, etc.)
- Produces a single output artifact
- No need to track state across compactions
- Examples: PR creator, deployment checklist, code review, `bmad-product-brief` (5-section coaching workflow)

### Complex Workflow Signals

- SKILL.md would exceed ~250 lines if everything stayed inline
- Each section is dense enough that combining them in one file hurts readability
- Long-running with context compaction risk (each carved file must self-contain)
- Routing logic in SKILL.md dispatches to `references/<descriptive-name>.md`
- Produces multiple artifacts across phases
- Examples: agent builder, module builder, project scaffolder, `bmad-prfaq` (each phase is dense)

## Module Context (Orthogonal)

Module context is asked for ALL types:

- **Module-based:** Part of a module. Uses `{modulecode}-{skillname}` naming. Config loading includes a fallback pattern — if config is missing, the skill informs the user that the module setup skill is available and continues with sensible defaults.
- **Standalone:** Independent skill. Uses `{skillname}` naming (no prefix required). Config loading is best-effort — load if available, use defaults if not, no mention of a setup skill.

The `bmad-` prefix is reserved for official BMad creations. User-created skills should not include it unless the user specifically requests it.
