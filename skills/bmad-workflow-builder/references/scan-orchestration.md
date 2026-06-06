# Scan Orchestration

This is how Analyze runs. It produces one HTML report from five LLM lenses, and it does so without per-subagent report files, without a `report-data.json`, and without an extract-and-reassemble round-trip. Deterministic scripts do the counting, the scanners read compact JSON instead of raw files, you consolidate their returns in-context, and one report-author fills the shell.

`{target-skill-path}` is the skill under analysis.

## Run the deterministic pre-pass first

Before any LLM lens sees the skill, run the deterministic scripts so the scanners read metrics rather than re-deriving them from raw text. Run these in parallel:

- `python3 scripts/prepass-prompt-metrics.py {target-skill-path}`: per-file token counts (via `scripts/count_tokens.py`, never line counts), frontmatter facts, and structural signals as JSON.
- `python3 scripts/prepass-workflow-integrity.py {target-skill-path}`: workflow-integrity checks as JSON.
- `python3 scripts/scan-path-standards.py {target-skill-path}`: path-convention lint (bare-paths-from-root, no double-prefix, no `./`).
- `python3 scripts/scan-scripts.py {target-skill-path}`: script-standards lint (PEP 723 metadata, shebangs, non-stdlib confirmation).

Collect the four JSON outputs. This is the compact picture the scanners work from, so they spend their context on judgment rather than on parsing files and counting tokens.

## Run the five lenses as parallel subagents

Hand each lens the pre-pass JSON and the skill path, and run them in parallel. Each lens loads `references/skill-quality-principles.md`, stays in its lane, and returns its findings to you in-context. No lens writes a file.

| Lens | File | Owns |
| --- | --- | --- |
| Leanness | `references/scan-leanness.md` | The three minimal-baseline tests: the core test, the defend-against-its-own-absence test, the outcome-vs-prescription test. |
| Architecture | `references/scan-architecture.md` | Structure, frontmatter, file topology, progressive disclosure, no-numbered-prefix enforcement, three-mode soundness. |
| Determinism | `references/scan-determinism.md` | The intelligence-placement boundary: intelligence leaks and determinism leaks, cross-referenced to script opportunities. |
| Customization | `references/scan-customization.md` | `customize.toml` surface economics, and confirmation that it is the only config mechanism present. |
| Enhancement | `references/scan-enhancement.md` | Missing named patterns to add and over-applied patterns to cut. |

Every lens returns the same JSON shape:

```json
{
  "lens": "leanness | architecture | determinism | customization | enhancement",
  "verdict": "<one line>",
  "findings": [
    {
      "id": "<lens>-<n>",
      "severity": "critical | high | medium | low",
      "title": "<short>",
      "location": "<file:region or file>",
      "evidence": "<what was observed>",
      "recommendation": "<the fix, including a cut where applicable>"
    }
  ]
}
```

The leanness lens adds two fields to any defend-against-absence finding: `proposed_smallest` (the minimal version of the section) and `predicted_delta` (what the smaller version would lose). Those two fields let you route the finding to the eval-runner's variant mode for a real cut-or-keep verdict instead of a guess.

## Consolidate, then hand off to the report-author

Merge the five returns into one findings list, keeping each finding's `id` so it stays traceable to its lens. Tally the severity counts for the summary. Then invoke the single `references/report-author.md` subagent with the consolidated findings, the subject path, and the summary counts. The report-author fills `assets/report-shell.html` by writing one JSON island that conforms to the report-data schema (schema_version 1) and injecting it into the shell. It does not invent findings; it renders what you hand it.

The shell parses its island in a loud try/catch and shows a visible error banner if parsing fails, never a blank page. An empty findings array renders an explicit "no findings" panel, so a clean skill produces a real report rather than nothing. Open the resulting HTML for the user.

## What is gone

There is no `generate-html-report.py`, no `extract-report-json.py`, and no `report-data.json` on disk. Scanners do not write per-subagent files. The pipeline is pre-pass scripts feeding the five lenses, you merging in-context, and one report-author filling the stable shell.
