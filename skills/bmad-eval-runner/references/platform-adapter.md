# Platform adapter

Everything runtime-specific in the eval-runner lives here, behind one seam. The rest of the skill, the scripts, the case format, the grader, and the modes are written against this seam and stay platform-agnostic. No model name is hardcoded anywhere; a model is just a value the adapter forwards if a runtime needs one, never a list this skill maintains.

An adapter provides three core things, plus two more only when trigger mode runs. If a new runtime can supply the three core values, the output-grading modes work against it unchanged; trigger mode also needs the two trigger keys described below.

## The three core things an adapter exposes

| Thing | What it is | Used by |
|---|---|---|
| invocation command | how to send an input to the runtime and get a completed run back | `run_evals.py`, `run_triggers.py` |
| auth env-var | the single environment variable name the runtime reads for its credential | clean-cwd setup |
| transcript schema | the on-disk shape of the run's event stream | `run_evals.py`, the grader |

### Invocation command

A template for running one input non-interactively and producing a transcript. The runner fills in the input (with any `state_prefix` already prepended) and the clean working directory, runs the command, and waits for completion. The command must run from the case's clean working directory so host shell config, prior runs, and ancestor instruction files do not bleed into the result. The only environment that crosses into that directory is the auth env-var below. There is no container, no terminal emulation, and no credential file staging.

For a baseline run the runner issues the same command twice from the same input: once with the skill available in the working directory and once with nothing wrapped around the model, so the bare-model floor is measured under identical conditions. For a variant run it issues the command against the full skill and against the `--variant-path` skill.

### Auth env-var

The name of the one environment variable the runtime reads for its credential. The runner forwards that variable's value from the host into the clean working directory and forwards nothing else. Naming the variable rather than baking in a provider keeps the seam honest: a different runtime declares a different variable name and everything upstream is unchanged.

### Transcript schema

The shape of the event stream the run writes, so `run_evals.py` knows where timing and token counts live and the grader knows how to read tool calls and the final message. An adapter declares:

- the file form and extension of the transcript (for example line-delimited JSON events),
- how to find a tool call in an event (the field that holds the tool name and the field that holds its arguments),
- how to find the final assistant message,
- where the completion notification reports timing and token usage, so `run_evals.py` can capture them to `timing.json` the moment the run finishes.

## Two more things for trigger mode

Trigger mode needs two keys beyond the core three, because it has to place a skill where the runtime will discover it and then recognize when that skill fired:

| Thing | What it is | Used by |
|---|---|---|
| skill_dir | the directory where the runtime discovers installed skills, so the synthetic skill can be staged for the run | `run_triggers.py` |
| load_signal | how a skill-load event appears in the transcript (a skill-invocation tool call, a read of the skill's entry file, or whatever the runtime emits on activation) | `run_triggers.py` |

These two stay idle for the output-grading modes (baseline, variant, quality); only trigger mode reads them.

## Trigger detection: "did the skill load"

Trigger mode does not measure output; it measures whether the description caused the skill to fire. Abstracted across runtimes, firing is one event: the skill loaded, expressed by `load_signal`. `run_triggers.py` stages a synthetic skill in `skill_dir` where the runtime discovers skills, sends each query through the invocation command, and checks the transcript for that load event. Each query runs several times because firing is probabilistic, and the trigger rate is the fraction of runs that loaded the skill.

## Adding a runtime

To support a new runtime, write an adapter that declares the invocation command, the auth env-var name, and the transcript schema, plus `skill_dir` and `load_signal` if you want trigger mode. Add no model list and no provider branch anywhere else; if a value beyond these is needed, it belongs in the adapter, not in a script or a prompt.
