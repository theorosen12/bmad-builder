# Build Process

This is one loop, not a sequence of phases. It carries Build and Edit, because an edit is the same loop pointed at a skill that already exists. The order below is the usual order of discovery, but nothing forces you to march through it; you pursue whichever outcome the conversation is ready for and you revisit earlier ones as the picture sharpens. Each outcome is a thing you want to be true, not a step you check off.

Load `references/skill-quality-principles.md` before you draft anything. It is the same institutional-knowledge file the scanners verify against, so building against it from the start is cheaper than fixing later. Load `references/standard-fields.md` for frontmatter and naming conventions. Load `references/producing-workflow-patterns.md` when the skill produces an artifact, runs across turns, or serves more than one intent (persona, intent modes, graceful degradation). Load `references/working-state-patterns.md` when the skill holds state across turns — it builds something revisable, or an existing skill already carries a `.memlog.md` or a structured working artifact. Load `references/complex-workflow-patterns.md` only when the skill is large enough to carve work out to `references/` (carve-out conventions, multi-stage routing, module metadata).

## Open by understanding why the user came

Before you read a single artifact, understand what the user is actually trying to get done and what "good" looks like to them. The open-floor invitation in activation does most of this work, so read what they dumped and mine the conversation history for the tools, the sequence, the corrections, and the inputs and outputs they have already shown you. Then ask only the gaps that remain. On an edit, this means reading the part of the existing skill the change touches and ignoring the rest, rather than re-deriving the whole spec.

## Harden the idea before you build it

A skill is cheap to generate and expensive to live with, so push on the idea before drafting rather than building the first description you hear. Pressure-test the shape: is this one skill or three, is it a skill at all or a one-off the user could just ask for directly, what is the single outcome and who consumes it, what real input does it run on, and where would it be thin or fail. Push back where the idea is half-formed, because a builder that accepts a vague idea ships a vague skill.

Calibrate to the user. When they arrive with a hardened, specific idea or say they want to move fast, confirm the shape and proceed without belaboring it. When the idea is raw, stay in the hardening conversation until the outcome and scope are clear, and for a genuinely exploratory idea offer `bmad-forge-idea` to pressure-test it or `bmad-brainstorming` to widen it before building.

Do not reduce this to a few multiple-choice questions and jump to building. The quiz-and-go feels efficient and skips the part that most determines whether the skill is worth building at all.

## Capture continuously into the memlog

As decisions and directions land, write them to `{target-skill-path}/.memlog.md` through `scripts/memlog.py` (`init` once when the target is named, then `append --type <decision|direction|assumption|gap|note|event>` as things happen). For a new skill, propose a kebab-case name when the user did not give one; renaming later is a logged decision, not a redo. The memlog is the canonical process memory, the source for resume, and the trail you audit at handoff so the user can confirm their thinking was handled the way they meant. Capture as you go, not in a batch at the end, because the value is in catching the reasoning while it is still fresh.

## Write the minimal outcome-driven version first

Draft the smallest skill that could possibly work. Hold it to four things: the role, the outcome, the consumer of the output, and any rule whose absence has already caused real damage. Everything else stays out until a comparison earns it. Apply the core test to every line you are tempted to write, because a model that already knows how to do the thing does not need to be told how. Default to writing the whole workflow inline in SKILL.md as named sections, and carve into `references/` with descriptive filenames (preferred over numbered prefixes) only when SKILL.md grows too large to scan in one pass.

## Run it on real input and reach for eval at the eval beat

A skill that has never run is a guess. Run the minimal version on the real, messy input the user actually has. This is the eval beat, and it is where you invoke `bmad-eval-runner`. Offer baseline mode to confirm the skill beats the bare model on the same input, because a skill that does not beat the bare model has no reason to exist. Offer trigger mode to harden the description against near-miss queries. Both are opt-in; surface them, explain what each one settles, and let the user decide.

`{workflow.evals_required}` overrides the opt-in default. When it is empty (default), the modes stay opt-in as above. When it is set, evals are a ship gate: `"baseline"` requires a passing baseline run before the build is done; `"any"` requires at least one eval case to exist and pass. If a required run fails or cannot be produced, the build is blocked, not shipped.

## Add scaffolding only when a comparison demands it

Do not add structure on a hunch. Add it only when a worse-on-a-named-dimension comparison shows the minimal version failing on something concrete, where you can say exactly what breaks without the addition. When you do add something, write what survives as a goal rather than a prescription, and reserve exact procedure for the few places where a wrong move costs something real. If you find yourself reaching for more structure, first ask whether a sharper outcome statement would have produced the same result; most of the time it would, so sharpen the sentence and skip the scaffold.

## Hunt for script opportunities throughout

This is the builder's differentiator, so keep it active the whole way through rather than treating it as a single checkpoint. Apply the determinism test and the signal-verb scan from `references/script-opportunities-reference.md` to anything the skill does, prefer native Python, and propose the pre-pass JSON pattern wherever the model would otherwise read raw files to extract facts a script could hand it. If eval transcripts show the model re-writing the same helper across runs, that is the signal to bundle it as a script once. List any non-stdlib dependency and confirm it with the user before relying on it.

## Decide customization with the explicit ask

Ask once, interactive only, and default to no: "Should this support end-user customization such as activation hooks, swappable templates, or output paths? If no, it ships fixed and anyone who needs a change forks it." Headless also defaults to no and emits a `customize.toml` only when the invocation explicitly asks for customization; log that decision in the memlog either way. When customization is accepted, bake the universal defaults and offer only the skill-specific points whose matching stages exist, following `references/customize-toml-guide.md`. When it is declined, emit no `customize.toml` and no resolver step, and the skill uses hardcoded paths throughout.

## Wire the universal shape, strip ceremony, and ship

Wire in the shape every producing skill shares: a working-state strategy chosen for this skill (memlog, a structured working artifact, both, or neither — see `references/working-state-patterns.md`), a distillation at finalize for skills whose output feeds downstream consumers, projections produced on demand rather than maintained, polish gated on the user's temperament, and a reviewer gate for skills that produce something substantive. Then strip the ceremony. Confirm the skill passes its own leanness scanner before you hand it off, because the builder has no standing to teach leanness while shipping bloat.

Two org gates apply before ship. Check SKILL.md against the token tiers in `references/skill-quality-principles.md` (Length guidance): warn the user between `{workflow.skill_md_token_desired}` and `{workflow.skill_md_token_budget}`, and if it is over `{workflow.skill_md_token_budget}`, lift sections to `references/` until it is back under. And verify the skill satisfies every directive in `{workflow.build_standards}`; treat each as a required criterion, not a suggestion, and resolve any miss before handoff. When the skill is lean, within budget, conformant, runs on real input, and the user has signed off on the memlog audit, ship it.

## Handoff

Interactive: before handing off, run the structural lint and path lint over the built skill and fix high or critical findings. Then show what was built and the lint results, and **offer to run the full validation — the Analyze lenses in `references/scan-orchestration.md` — over the new skill**. This is the default next step, not one option among several: offer it explicitly and proactively rather than waiting for the user to ask. If the user accepts, run the Analyze flow and **open the resulting HTML report for them when it finishes** — that flow produces and opens the report, so do not stop at summarizing findings in chat. Then walk the memlog audit at `{target-skill-path}/.memlog.md` so they confirm their reasoning was handled the way they intended. Once the skill is delivered and the user has been told it is ready, run `{workflow.on_complete}` if non-empty (a string scalar is one instruction, an array is a sequence run in order).

Headless (`{headless_mode}=true`): call `set-complete` on the memlog and emit JSON only.

```json
{
  "status": "complete",
  "intent": "build",
  "skill": "{target-skill-path}",
  "memlog": "{target-skill-path}/.memlog.md"
}
```

Use `"intent": "edit"` for an existing skill. If the run is blocked by ambiguous intent that could not be inferred or by lint failures that would not clear, replace `"complete"` with `"blocked"` and add `"reason": "<one-line cause>"`. The memlog carries the detail.
