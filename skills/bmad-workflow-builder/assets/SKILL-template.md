---
name: {skill-name}
description: {one-line summary plus the trigger phrases that should route here, e.g. "Use when the user says X or wants to Y"}
---

<!-- BUILDER SCAFFOLD GUIDANCE — DELETE THIS WHOLE COMMENT BLOCK BEFORE SHIPPING.

This is a starting point, not a shape to fill in mechanically. Keep the role
paragraph, the activation block, and whatever the skill actually needs. Cut the
rest. Every surviving line should beat its own absence.

Pick the archetype that matches what you are building and keep only its parts:

- One-shot action. The skill does a single thing and returns. Keep the role
  paragraph and a short outcome statement. Drop multi-stage routing, memlog, and
  resume. Most skills are this; resist adding more.

- Producer of a durable artifact (brief, PRD, report, deck). Keep memlog as the
  process memory, a finalize beat that distills the memlog into the artifact, and
  the output-path handling. This is the archetype that earns memlog.

- Multi-intent router. The skill handles a few related jobs behind one entry.
  Keep an intent table that routes to references, and name the stages with
  descriptive words, never numbered prefixes.

Customization: only add the resolver activation step and reference
{workflow.<name>} values if the author accepted customize.toml. If they declined,
use hardcoded paths and drop the resolver step entirely.

-->

# {skill-name}

{One paragraph: who the skill is acting as, the outcome it produces, and who
consumes that output. Write it once; do not restate it lower down.}

## Conventions

- Bare paths (e.g. `references/guide.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present). Use sensible defaults for anything missing rather than requiring configuration.

<!-- Keep step 2 only for artifact-producing skills that carry process memory. -->
2. Resume check. Look for an existing `.memlog.md` in the run folder. If one is found, read it once to rebuild state and continue append-only; otherwise initialize a new memlog with `python3 scripts/memlog.py init --path <run-folder>/.memlog.md`.

<!-- Keep step 3 only if the author accepted customize.toml. -->
3. Resolve the `workflow` block by reading `customize.toml`, then the team and user override files in that order, applying the structural merge rules. Reference resolved values as `{workflow.<name>}` everywhere below; never hardcode a path beside a declared scalar.

## {Body}

{The body is whatever the skill needs and nothing more. State each beat as the
outcome you want, reserving exact procedure for the few places a wrong move costs
something. Name stages with descriptive words, never numbered prefixes.}
