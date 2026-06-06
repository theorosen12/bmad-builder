---
name: build-process
description: The single Process loop for building or rebuilding a BMad agent. One goal-driven loop, not a phase sequence, covering discovery, the minimal version, the capability fork, the eval beat, the customization decision, and ship.
---

**Language:** Use `{communication_language}` for all output.

# Build Process

This is one loop, not a sequence of phases. It carries Create and Rebuild, because a rebuild is the same loop pointed at an existing agent treated as a description of intent rather than a template to copy. The order below is the usual order of discovery, but nothing forces you to march through it; pursue whichever outcome the conversation is ready for and revisit earlier ones as the picture sharpens. Each outcome is a thing you want to be true, not a box to tick.

Load `references/agent-quality-principles.md` before you draft anything, because it is the same bar the lenses verify against and building to it from the start is cheaper than fixing later. It cedes the universal core to `references/prompt-quality-canon.md`, so hold the canon's tests while you work and load it when you author or refine any capability. Load `references/agent-type-guidance.md` for the gradient and the routing questions, and `references/standard-fields.md` for field definitions, naming, and path rules.

## Understand why the user came

Before you read a single artifact, understand who this agent is, how it should make the user feel, the core outcome it serves, and the one thing it must get right. The open-floor invitation in activation does most of this, so read what the user dumped and mine the conversation history first, then ask only the gaps that remain. On a rebuild, read the old agent to extract who it is and what it achieves, and deliberately leave its verbosity, structure, and mechanical procedures behind.

Type emerges here from natural questions, not a menu. Ask whether the agent needs to remember between sessions, which separates stateless from memory; whether the user should be able to teach it new capabilities after install, which gates evolvable capabilities; and whether it should operate on its own when no one is watching, which adds PULSE and makes it autonomous. Confirm the read back in plain words, and for a memory agent confirm relationship depth, since a deep partnership wants a calibration First Breath while a focused domain tool wants a warmer but quicker configuration setup.

## Capture into the memlog throughout

As decisions and directions land, write them to `{target-agent-path}/.memlog.md` through `scripts/memlog.py`: `init --path {target-agent-path}/.memlog.md` once when the target is named, then `append --path {target-agent-path}/.memlog.md --type <decision|direction|assumption|gap|note|event> --text "..."` as things happen. For a new agent, propose a kebab-case name when the user did not give one; renaming later is a logged decision, not a redo. This `.memlog.md` is the builder's process trace and lives beside the built agent's SKILL.md. It is not the sanctum. The sanctum is the built agent's own runtime memory at `{project-root}/_bmad/memory/{skillName}/`, written by the agent at runtime, never by this log. A memlog entry records a build decision and sanctum content is the agent's living state, so neither ever holds the other's material. Capture as you go so the reasoning is caught while fresh, because the memlog is the resume source and the trail you walk with the user at handoff.

## Write the minimal outcome-driven version first

Draft the smallest agent that could work. Hold the persona and capabilities to the role, the core outcome, the consumer of the output, and any rule whose absence has already caused real damage. Apply the canon's core test to every capability-prompt line you are tempted to write, because a capable model given the persona and the outcome does not need to be told how. The persona is the exception the canon's leanness bar does not touch: write the voice, the communication-style examples, the domain framing, and the design rationale out in full, because the persona is the path the model takes through every capability and a flatter version is a worse outcome, not a leaner one.

### Fork on capability versus skill reference

For each capability the agent needs, decide which of two forms it takes, applying the criteria identically now and at the agent's own evolve time:

- Reference an installed skill when a skill already covers the capability. Suggest the reference, and always ask before installing anything. When external skills are in play, suggest `bmad-module-builder` so the agent ships bundled with its dependencies.
- Author an internal capability only when it is genuinely novel, or when it is tightly coupled to the persona such that a generic skill would lose the agent's voice or context.

When you author an internal capability, route the authoring through the canon and the `assets/capability-authoring-template.md` mechanics, hold the canon's tests while you write the body, and give every internal prompt-type capability its frontmatter (name, description, code, added, type) and an outcome-focused body. The internal capability is a skill that happens to live inside an agent; the only thing that relaxes is that the persona supplies the how.

## Hunt for script opportunities throughout

Keep this active the whole way rather than treating it as one checkpoint. Apply the determinism test and the signal-verb scan from `references/script-opportunities-reference.md` to anything the agent does, prefer native Python, and follow `references/script-standards.md` for PEP 723 inline metadata, `uv run` invocation, and graceful fallback when a dependency is absent. The sanctum scaffold and the memory index are fertile sources, and a transcript that shows the model rewriting the same helper across runs is the signal to bundle it once. List any non-stdlib dependency and confirm it with the user before relying on it.

## Reach for eval at the eval beat

An agent that has never run is a guess. At the eval beat, invoke the standalone `bmad-eval-runner` against the built agent, which is a directory containing SKILL.md that the runner already accepts; do not fork any eval logic. Offer the modes that fit and let the user decide:

- Trigger mode hardens the activation description against near-miss queries.
- Baseline mode confirms the agent beats the bare model on the same input, since an agent that does not has no reason to exist.
- Quality or variant mode settles a finding about a single capability prompt by running a smaller version against the same input, which is how a defend-against-absence question gets answered rather than argued.

## Decide customization with the explicit ask

Ask once, interactive only, and default to no: "Should this agent expose override hooks such as activation steps or persistent facts so teams can customize it without forking?" Log the answer to the memlog either way. The archetype shapes the default. Memory and autonomous agents default to no because the sanctum is already their customization surface and a TOML override competes with it; offer the opt-in only when the user has a concrete pre-sanctum-load need such as an org-mandated compliance preload. Stateless agents are the natural candidate, so offer the opt-in there and accept either answer. Headless defaults to no unless the invocation explicitly asks for customization.

Every agent still emits a `customize.toml`, because its always-present `[agent]` metadata block (code, name, title, icon, description, agent_type) is the install-time roster contract the installer reads to populate `module.yaml`. customize.toml is the only build-time config surface, and First Breath and init-sanctum are runtime sanctum initialization rather than build config, so they stay out of it; `references/agent-quality-principles.md` carries the forbidden-mechanisms list. When the opt-in is yes, retain the override block, append any swappable scalars following the `*_template` / `*_output_path` / `on_<event>` conventions, and add the resolver activation step to SKILL.md so it reads scalars as `{agent.<name>}`. When it is no, emit metadata only and SKILL.md uses hardcoded paths.

## Strip ceremony and ship

Confirm the agent passes its own leanness bar before handoff, because the builder has no standing to teach leanness while shipping bloat. The leanness pass cuts ceremony from capability prompts and never flattens the persona. Ship the canon copy into the built agent at its `references/prompt-quality-canon.md` exactly as the vendored scripts are copied, so an evolving agent resolves the standard from its own root. Run the lint gate over the built agent (`scripts/scan-path-standards.py` and `scripts/scan-scripts.py` in parallel, fixing high or critical findings and re-running), and run unit tests if the built agent carries scripts.

## The output tree

Every agent shares one output tree. The archetype changes which parts are present and the SKILL.md weight, captured in the delta table below rather than three separate trees.

```
{agent-name}/
├── SKILL.md                       # Identity and activation routing (full for stateless, lean bootloader for memory/autonomous)
├── customize.toml                 # [agent] metadata always; override block only when opted in
├── references/
│   ├── prompt-quality-canon.md    # Shipped canon copy (always), resolves from the agent root
│   ├── {capability}.md            # Internal capability prompts, outcome-focused (as needed)
│   ├── first-breath.md            # Memory/autonomous only, from the calibration or configuration template
│   ├── memory-guidance.md         # Memory/autonomous only
│   └── capability-authoring.md    # Evolvable agents only; mechanics that defer the bar to the canon
├── assets/                        # Sanctum templates for memory/autonomous; static starter files otherwise
│   ├── INDEX-template.md          # Sanctum map (memory/autonomous)
│   ├── PERSONA-template.md        # Persona seed (memory/autonomous)
│   ├── CREED-template.md          # Values and standing orders incl. the canon pull-in (memory/autonomous)
│   ├── BOND-template.md           # Owner-relationship seed (memory/autonomous)
│   ├── MEMORY-template.md         # Long-term memory seed, starts empty (memory/autonomous)
│   ├── CAPABILITIES-template.md   # Capability registry (memory/autonomous)
│   └── PULSE-template.md          # Autonomous only
└── scripts/
    └── init-sanctum.py            # Memory/autonomous only, scaffolds the sanctum deterministically
```

| Concern | Stateless | Memory | Autonomous |
| --- | --- | --- | --- |
| SKILL.md weight | Full identity: overview, mission, persona, principles, conventions, on-activation, capabilities table | Lean bootloader (~400 tokens as a guardrail): identity seed, Three Laws, Sacred Truth, mission, activation routing | Same lean bootloader, plus the Quiet Rebirth activation path |
| Sanctum | None | INDEX, PERSONA, CREED, BOND, MEMORY, CAPABILITIES at `{project-root}/_bmad/memory/{skillName}/` | Same sanctum |
| First Breath | None | Calibration or configuration, seeded with domain territories | Same, and PULSE is explained on first activation |
| PULSE | None | None | PULSE.md: default wake behavior, named task routing, frequency, quiet hours |
| init-sanctum.py | None | Present, parameterized to the agent | Present |
| Activation | Single flow: load config, greet, present capabilities | Three paths: no sanctum runs init then First Breath; normal batch-loads the sanctum and becomes itself; runtime headless runs the Quiet Rebirth | Same three paths; the runtime headless path is the Quiet Rebirth where memory curation is always the first priority |
| customize override surface | Offered, either answer accepted | Default no | Default no |

The Quiet Rebirth in the runtime-headless row is the built autonomous agent waking on its own schedule. It is not the builder's `--headless` flag, which only makes this build process non-interactive.

## Handoff

Interactive: present what was built (location, structure, first-run behavior, and the capabilities registered by code and name), show the lint results, and walk the user through the memlog at `{target-agent-path}/.memlog.md` so they confirm their reasoning was handled as they meant. For memory agents, explain the First Breath experience in plain words, note that PERSONA, CREED, and BOND ship seeded while MEMORY starts empty, and explain that `uv run scripts/init-sanctum.py <project-root> <skill-path>` runs before the first conversation. For autonomous agents, also explain PULSE behavior and scheduling. Offer Analyze over the new agent as the natural next step.

Headless (`{headless_mode}=true`): call `set-complete` on the memlog and emit JSON only.

```json
{
  "status": "complete",
  "intent": "create",
  "agent": "{target-agent-path}",
  "agent_type": "stateless|memory|autonomous",
  "memlog": "{target-agent-path}/.memlog.md"
}
```

If the run is blocked by ambiguous intent that could not be inferred or by lint failures that would not clear, replace `"complete"` with `"blocked"` and add `"reason": "<one-line cause>"`. The memlog carries the detail.
