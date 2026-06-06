---
name: capability-authoring
description: Mechanics for creating and registering learned capabilities
---

# Capability Authoring

When your owner wants you to learn a new ability, you create a capability together. This guide covers the mechanics: the shapes a capability can take, the frontmatter each prompt carries, the creation flow, and how a new capability gets registered.

The quality bar is not here. Your "Author to the standard" standing order has you load the prompt-quality canon before you write or refine anything, so hold its tests while you work. The shipped copy is `references/prompt-quality-canon.md`, with `{siteBase}/explanation/outcome-driven-prompt-quality/` as the fallback. This file does not restate those tests, so that there is one authority and it cannot drift.

## Capability Types

A capability can take several forms.

### Prompt (default)
A markdown file with guidance on what to achieve. Best for judgment-based tasks where you need flexibility.

```
capabilities/
└── {example-capability}.md
```

### Script
A Python or bash script for deterministic tasks such as calculations, file processing, data transformation, or API calls. Create the script alongside a short markdown file that says when to run it and what to do with the results.

```
capabilities/
├── {example-script}.md          # When to run, what to do with results
└── {example-script}.py          # The actual computation
```

### Multi-file
A folder with multiple files for a more involved capability, such as a mini-workflow with several steps plus reference material or templates.

```
capabilities/
└── {example-complex}/
    ├── {example-complex}.md     # Main guidance
    ├── structure.md             # Reference material
    └── examples.md              # Examples for tone/format
```

### External Skill Reference
Point to an existing installed skill rather than reinventing it. If you discover a skill that would serve your owner well, suggest it, and always ask before installing.

```markdown
## Learned
| Code | Name | Description | Source | Added |
|------|------|-------------|--------|-------|
| [XX] | Skill Name | What it does | External: `skill-name` | YYYY-MM-DD |
```

## Prompt File Frontmatter

Every capability prompt file carries this frontmatter:

```markdown
---
name: {kebab-case-name}
description: {one line, what this does}
code: {2-letter menu code, unique across all capabilities}
added: {YYYY-MM-DD}
type: prompt | script | multi-file | external
---
```

The body is the capability prompt itself. Author it against the canon you loaded.

## Creating a Capability (The Flow)

1. Owner says they want you to do something new.
2. Explore what they need through conversation; don't rush to write.
3. Draft the capability and show it to them.
4. Refine based on feedback.
5. Save to `capabilities/` as a file or folder depending on type.
6. Register it in CAPABILITIES.md by adding a row to the Learned table.
7. Register it in INDEX.md by noting the new file under "My Files".
8. Confirm: "I'll remember how to do this next session. You can trigger it with [{code}]."

## Refining and Retiring

When you refine a capability after feedback, update the file in place and log the refinement in the session log. When a capability is no longer useful, remove its row from CAPABILITIES.md but keep the file so the owner can bring it back, and note the retirement in the session log. Whether a capability still earns its place is a canon question, so apply the canon's retirement test rather than a rule restated here.
