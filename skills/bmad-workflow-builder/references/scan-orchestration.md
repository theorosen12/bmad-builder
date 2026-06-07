# Scan Orchestration

How Analyze runs: a deterministic pre-pass, five LLM lenses in parallel, you merge their findings in-context, and one report-author fills the shell. `{target-skill-path}` is the skill under analysis.

## Run the deterministic pre-pass first

Run these in parallel so the lenses read metrics instead of re-deriving them:

- `python3 scripts/prepass-prompt-metrics.py {target-skill-path}`: per-file token counts (via `scripts/count_tokens.py`), frontmatter facts, and structural signals as JSON.
- `python3 scripts/prepass-workflow-integrity.py {target-skill-path}`: workflow-integrity checks as JSON.
- `python3 scripts/scan-path-standards.py {target-skill-path}`: path-convention lint (bare-paths-from-root, no double-prefix, no `./`).
- `python3 scripts/scan-scripts.py {target-skill-path}`: script-standards lint (PEP 723 metadata, shebangs, non-stdlib confirmation).

## Run the five lenses as parallel subagents

Hand each lens the pre-pass JSON and the skill path. Each loads `references/skill-quality-principles.md` and returns its findings to you in-context.

| Lens | File | Owns |
| --- | --- | --- |
| Leanness | `references/scan-leanness.md` | The three minimal-baseline tests: the core test, the defend-against-its-own-absence test, the outcome-vs-prescription test. |
| Architecture | `references/scan-architecture.md` | Structure, frontmatter, file topology, progressive disclosure, three-mode soundness. |
| Determinism | `references/scan-determinism.md` | The intelligence-placement boundary: intelligence leaks and determinism leaks, cross-referenced to script opportunities. |
| Customization | `references/scan-customization.md` | `customize.toml` surface economics, and confirmation that it is the only config mechanism present. |
| Enhancement | `references/scan-enhancement.md` | Missing named patterns to add and over-applied patterns to cut. |

Each lens returns the standard findings JSON defined in its own file. The leanness lens also returns `proposed_smallest` and `predicted_delta` on defend-against-absence findings, which you can route to the eval-runner's variant mode for a cut-or-keep verdict.

## Apply the org gates

Two customize-driven gates run alongside the lenses, only when configured:

- **`{workflow.build_standards}`** — if non-empty, check the skill against each directive (`skill:`, `file:`, or plain text) and fold any miss into the findings as a conformance finding.
- **`{workflow.evals_required}`** — if set, confirm the skill has the required evals (`"baseline"` or `"any"`); if not, add a high-severity finding.

## Consolidate, then hand off to the report-author

Merge the lens returns into one findings list, keep each finding's `id`, and tally the severity counts. Invoke `references/report-author.md` with the consolidated findings, the subject path, and the summary counts, then open the resulting HTML report for the user. The HTML report is the deliverable of Analyze — always produce and open it; do not replace it with a chat summary of the findings.
