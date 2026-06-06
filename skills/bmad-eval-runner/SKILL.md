---
name: bmad-eval-runner
description: Run a skill's evals and report results. Use when the user wants to evaluate a skill, run evals, benchmark a skill, validate triggers, optimize a description, or grade skill outputs.
---

# Skill Eval Runner

You run a skill's evals and report what they say. The user wants signal, not theatre, so cite specific findings, surface evals that pass for trivial reasons, and never widen a tolerance to make a run look like it succeeded.

The runner is platform-agnostic. Everything runtime-specific (how a skill is invoked, where its auth comes from, what its transcript looks like) lives behind the adapter seam described in `references/platform-adapter.md`. No model name is hardcoded anywhere in this skill.

## The four modes

Each mode answers a different question about a skill. Pick the one that matches what the user is asking, or run several.

| Mode | Question it answers | Script / reference |
|---|---|---|
| baseline | Does the skill beat the bare model on the same input? | `references/eval-format.md`, `scripts/run_evals.py` |
| variant | Does a section earn its place, or does a stripped version do as well? | `references/eval-format.md`, `scripts/run_evals.py` |
| quality | Does the output meet the named rubric? | `references/grader.md`, `references/eval-format.md` |
| trigger | Does the description fire on the right queries and stay quiet on the rest? | `references/platform-adapter.md`, `scripts/run_triggers.py` |

Baseline runs the input twice in the same turn, once with the skill and once against the bare model, so the bare model is the long-term floor. Variant runs the full skill against a stripped smallest-version of itself to settle whether a section is doing real work. Quality grades one config's output against a rubric with the read-only grader. Trigger measures real firing through the adapter and can optimize the description across rounds; the optimization loop lives in `references/description-optimization.md`.

A case is `input + rubric + optional state_prefix`. The `state_prefix` is a bracketed prime prepended to the input that places the skill mid-workflow in a single shot, so one input can exercise any turn without a multi-turn simulator. The full case format and the strong-versus-weak expectation taxonomy are in `references/eval-format.md`.

## Args

- Positional: a path to the skill being evaluated (directory containing `SKILL.md`).
- `--evals <path>`: explicit path to the cases file. If omitted, discover.
- `--mode baseline|variant|quality|trigger`: which mode to run. May be repeated.
- `--variant-path <path>`: for variant mode, the stripped or prior-version skill to compare against.
- `--project-root <path>`: root of the project the skill belongs to. Default: walk up from the skill path looking for `_bmad/` or `.git/`.
- `--output-dir <path>`: where run folders are written. Default: `{bmad_builder_reports}/eval-runs/` if configured, else `~/bmad-evals/`.
- `--runs <n>`: repeats per case for the variance benchmark. Default: 1 for a single check, higher when the user wants a stable mean.
- `--headless` / `-H`: non-interactive; emit final JSON only.

## On activation

1. Resolve config the way `bmad-workflow-builder` does (`{project-root}/_bmad/config.yaml` then `config.user.yaml`, falling back to `bmb/config.yaml`). Resolve `{user_name}`, `{communication_language}`, `{bmad_builder_reports}` and apply them through the session.

2. If `--headless` was passed, set `{headless_mode}=true`, skip every confirmation below, pick the safest defaults, and proceed.

3. Resume check: glob the output dir for an in-progress run's `.memlog.md`. If one exists and matches this skill, read it once to rebuild state, then continue append-only. Capture decisions and direction changes into the run's memlog through `scripts/memlog.py` as they land.

4. Locate the skill and verify `<skill-path>/SKILL.md` exists. Halt with a clear error if it does not.

5. Load the adapter for the current runtime from `references/platform-adapter.md`. This gives you the invocation command, the auth env-var to forward, and the transcript schema to read.

6. Discover the cases file. Look at `--evals` first, then `<skill-path>/evals/`, then `<skill-path>/../../evals/<skill-name>/`, then `<project-root>/evals/<skill-name>/`, then anywhere under `<project-root>/evals/`. Take the first match. If nothing is found, halt and say so; the runner does not invent cases.

7. Confirm the run summary (skill, cases found, modes, output dir) unless headless, then execute.

## Run execution

Run each case in a clean working directory so the host shell config, prior runs, and ancestor instruction files do not bias the result. The clean-cwd setup is part of the adapter seam; there is no container, no terminal emulation, and no credential staging beyond forwarding the adapter's auth env-var.

For baseline, variant, and quality modes, call `python3 {skill-root}/scripts/run_evals.py` with the resolved arguments and the adapter. The script applies any `state_prefix` to the input before invoking, runs the configured invocations (skill, bare model, or variant), and writes a per-case folder. It captures timing and token counts the moment each invocation completes and writes them to `timing.json` immediately, so a later crash never loses the measurement.

For trigger mode, call `python3 {skill-root}/scripts/run_triggers.py`. It stages a synthetic skill where the runtime discovers skills, sends each query through the adapter, and detects the skill-load event. Each query runs several times for stability. When the user wants to optimize the description rather than just measure it, follow `references/description-optimization.md`.

For quality mode, spawn the grader described in `references/grader.md` per case. The grader is read-only against the run folder, returns `{text, passed, evidence}` per expectation, gives no partial credit, and flags weak or non-discriminating assertions. Relay that feedback.

When `--runs` is greater than one, call `python3 {skill-root}/scripts/aggregate_benchmark.py` to produce the mean, sample standard deviation, min, max, and the delta between configs.

## Artifacts

Every run writes a dated run folder under the output dir, and those artifacts are permanent. Each case folder holds its prompt, transcript, any files the skill wrote, `timing.json`, and the grading when quality mode ran. Never delete, overwrite, or rotate a run folder; disk usage is the user's call. The run's `.memlog.md` records the decisions and deltas so a resumed or audited run reads back cleanly.

Tell the user where the run folder is when you finish.

## Outcomes

- The run reflects the skill's behavior in a clean working directory, not the behavior of the host shell with its memories and configs.
- Timing and token counts land on disk the moment they are measured.
- Failures cite specific expectations with evidence, and a pass that looks superficial is flagged rather than papered over.
- A baseline run that the skill no longer wins points to retiring the skill, not patching it.
