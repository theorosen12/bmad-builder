# Scan Orchestration

How Analyze runs: a deterministic pre-pass, five LLM lenses in parallel, you merge and synthesize in-context, and a script renders the report. `{target-skill-path}` is the skill under analysis.

## Run folder

Each analyze run owns `{target-skill-path}/.analysis/<YYYY-MM-DD-HHmm>/` (create it first). It receives `findings.json`, `skill-analysis-report.html`, and `skill-analysis-report.md`.

## Run the deterministic pre-pass first

Run these in parallel so the lenses read metrics instead of re-deriving them:

- `python3 scripts/prepass-prompt-metrics.py {target-skill-path}`: per-file token counts (via `scripts/count_tokens.py`), frontmatter facts, and structural signals as JSON.
- `python3 scripts/prepass-workflow-integrity.py {target-skill-path}`: workflow-integrity checks as JSON.
- `python3 scripts/scan-path-standards.py {target-skill-path}`: path-convention lint (bare-paths-from-root, no double-prefix, no `./`).
- `python3 scripts/scan-scripts.py {target-skill-path}`: script-standards lint (PEP 723 metadata, shebangs, non-stdlib confirmation).

## Run the five lenses as parallel subagents

Hand each lens the pre-pass JSON and the skill path. Each loads the bar its own spec file names (the canon, the principles file, or its lane's spec) and returns its findings to you in-context.

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

## Synthesize and render

Merge the lens returns into one findings list, keeping each finding's `id`. Then author the synthesis layer yourself — grade, summary, themes, strengths, recommendations — per the contract in `references/report-author.md`; you hold every finding in context, so no subagent is involved. Write the island object to `{run-folder}/findings.json` and render:

```bash
python3 scripts/render_report.py {run-folder}/findings.json --shell assets/report-shell.html -o {run-folder}/skill-analysis-report.html --md {run-folder}/skill-analysis-report.md
```

If the script refuses, fix `findings.json` and re-run; never hand-edit the HTML. Open the HTML report for the user — it is the deliverable of Analyze; do not replace it with a chat summary of the findings.

## Record the run

Append one memlog event carrying the grade (init the memlog first if `{target-skill-path}/.memlog.md` does not exist):

```bash
python3 scripts/memlog.py append --path {target-skill-path}/.memlog.md --type event --text "analyze: grade <grade>, <c> critical / <h> high / <m> medium / <l> low, report .analysis/<timestamp>/skill-analysis-report.html"
```

## Present

**IF `{headless_mode}=true`:** emit

```json
{
  "headless_mode": true,
  "status": "complete",
  "skill": "{target-skill-path}",
  "grade": "excellent | good | fair | poor",
  "html_report": "{target-skill-path}/.analysis/<timestamp>/skill-analysis-report.html",
  "md_report": "{target-skill-path}/.analysis/<timestamp>/skill-analysis-report.md",
  "memlog": "{target-skill-path}/.memlog.md",
  "counts": { "critical": 0, "high": 0, "medium": 0, "low": 0 }
}
```

**IF interactive:** present the grade, the one-line verdict, the severity tally, and the top themes. Point to the HTML report path, say it opened, and offer to walk through findings, apply a fix, or route a leanness finding's `proposed_smallest` to a variant eval.
