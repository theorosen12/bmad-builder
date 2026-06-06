# Script Opportunities Reference

Hunting for deterministic work to push out of prompts and into native Python is the builder's differentiator. Neither competing skill-creator does it. A prompt that asks the model to count, parse, validate, or diff is paying generation cost on every run for an answer a script gives once, exactly, for free. The hunt is always on, not a finalize-time afterthought.

This file covers the determinism test that decides script-or-prompt, the signal-verb scan that surfaces candidates inside a draft, the opportunity categories, the pre-pass JSON pattern, and the transcript-detected repeated-work signal that eval runs expose. Reference `references/script-standards.md` for the full authoring conventions (PEP 723, output schema, testing).

## The line that decides it

Scripts handle deterministic operations. Prompts handle judgment. If a check has clear pass/fail criteria and the same input always yields the same output, it belongs in a script, and a prompt that does it instead is friction that does not beat its own absence.

## The determinism test

Run three questions over any step you are about to write as a prompt instruction:

1. Given identical input, will it always produce identical output? If yes, it is a script candidate.
2. Could you write a unit test with an expected output? If yes, it is definitely a script.
3. Does it require interpreting meaning, tone, or context? If yes, keep it as a prompt.

The boundary between the two:

| Scripts handle | Prompts handle |
| --- | --- |
| Fetch, transform, validate | Interpret, classify when ambiguous |
| Count, parse, compare | Create, decide on incomplete info |
| Extract, format, check structure | Evaluate quality, synthesize meaning |

## The signal-verb scan

When a draft's instructions contain these verbs, look for a script first: validate, count, extract, convert, transform, compare, scan for, check structure, against schema, graph or map dependencies, list all, detect pattern, diff or changes between. Each one names work that produces the same answer every time, so paying a model to do it is waste.

## Opportunity categories

| Category | What it does | Example |
| --- | --- | --- |
| Validation | Check structure, format, schema, naming | Confirm frontmatter fields exist |
| Data extraction | Pull structured data without interpreting meaning | Extract every `{variable}` reference from markdown |
| Transformation | Convert between known formats | Markdown table to JSON |
| Metrics | Count, tally, aggregate | Token count per file via count_tokens.py |
| Comparison | Diff, cross-reference, verify consistency | Cross-ref prompt names against SKILL.md references |
| Structure checks | Verify directory layout, file existence | Confirm a skill folder has its required files |
| Dependency analysis | Trace references, imports, relationships | Build a skill reference graph |
| Pre-processing | Extract compact data from large files before the model reads them | Pre-extract file metrics into JSON for a scanner |
| Post-processing | Verify model output meets structural requirements | Confirm generated YAML parses |

## The pre-pass JSON pattern

When a workflow stage would otherwise have the model read raw files to gather facts (line counts, token counts, frontmatter values, file inventories, reference lists), write a pre-pass script that does the reading and emits compact JSON, then have the prompt consume the JSON instead. The model reasons over metrics rather than burning context on raw bytes, the facts are exact rather than estimated, and the stage runs cheaper. The Analyze scanners use this pattern: deterministic pre-pass and lint scripts run first and hand each scanner compact JSON, so the scanners read numbers, not whole files.

## The transcript-detected repeated-work signal

The eval-runner produces transcripts when a skill runs on real input. Read them for the same helper being re-derived run after run. If the model writes a small parser, a counter, a format converter, or a validation snippet inline on turn after turn, that work is deterministic by definition (it produces the same code each time) and it is paying generation cost every run. Bundle it once as a script the skill calls, and the repeated inline derivation disappears.

This is the strongest possible evidence for a script, because it is not a guess about what the model might do, it is the model demonstrably doing the same deterministic thing repeatedly. When a baseline or quality eval run shows this pattern, the recommendation is a named script, and the next eval run should show the inline derivation gone.

## Native Python is the default

All script logic is native Python so it runs the same on macOS, Linux, and Windows or WSL. The standard library covers most needs: `json`, `pathlib`, `re`, `argparse`, `collections`, `difflib`, `ast`, `csv`, `xml`. Avoid bash for logic, so no piping, `jq`, `grep`, `sed`, `awk`, `find`, `diff`, or `wc` inside a script; use the Python equivalent. The safe shell surface is `git`, `gh`, `uv run`, the node package managers, and `mkdir -p`.

Non-stdlib dependencies are declared with PEP 723 inline script metadata and run with `uv run`, which resolves the declared deps without a separate install step:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["tiktoken"]
# ///
```

Every script must still run under a plain `python3` invocation, so any non-stdlib dependency needs a graceful fallback when the import fails (count_tokens.py is the model: tiktoken when present, chars-over-four when absent). At build time, confirm the non-stdlib dependencies are available in the target environment before relying on them, and log the confirmation. Confirming script dependencies is a legitimate build check, not a customization surface.

## The --help pattern

Every script declares PEP 723 metadata and implements `--help`. A prompt can point at `scripts/foo.py --help` instead of inlining the interface, which keeps the interface defined in one place and saves prompt tokens.

## Output and authoring conventions

Scripts emit structured JSON and follow the authoring checklist (PEP 723 metadata, skill-path argument, `-o` for output, diagnostics to stderr, exit codes 0 pass / 1 fail / 2 error, no interactive prompts, no network, tests under `scripts/tests/`). The full schema and checklist live in `references/script-standards.md` so they stay defined once.
