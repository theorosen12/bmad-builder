# Report Contract: Findings Schema and Render

There is no report-author subagent. You — the Analyze orchestrator — already hold every lens return in context, so you author the synthesis, write one `findings.json`, and let `scripts/render_report.py` produce the HTML deterministically. Never hand-write report HTML, and never edit the rendered file.

## Author the synthesis layer

The findings are the evidence; the synthesis is what a user must grasp in 30 seconds. All synthesis fields are yours to write:

- `verdict` — one line naming the overall state and the one or two findings that matter most. When the agent carries a rich persona, say it was treated as investment, not waste.
- `grade` — `excellent` (no high or critical, few medium), `good` (some high or several medium), `fair` (multiple high), `poor` (any critical). Lowercase.
- `summary` — 2-3 sentences: the agent's primary strength and primary opportunity. This is the first thing the user reads.
- `themes` — findings clustered by shared root cause, not by file. Ask: "if I fixed X, how many findings across lenses would that resolve?" 3-5 themes; findings that fit no theme stay ungrouped in `findings` only. Each theme's `action` is one coherent fix instruction for the whole cluster, and `finding_ids` lists the constituent findings so the report can show them under the theme.
- `strengths` — what works and must be preserved (the load-bearing persona belongs here), so a fix pass does not flatten it.
- `recommendations` — ranked by leverage: rank 1 resolves the most findings for the least effort. `resolves` lists the finding ids it would clear.

## The agent blocks

Optional portrait-and-context blocks, built from the pre-pass and what the lenses observed:

- `agent_profile` — `name`, `title`, `icon`, `agent_type` (straight from the pre-pass), one-line `mission`. Drawn from the agent's `[agent]` metadata.
- `capabilities` — `{ name, kind, note }` per capability, where `kind` is the form (prompt, script, multi-file, external skill) and `note` is one line on what it does.
- `detailed_analysis` — keyed by lens name, each value that lens's one-line `verdict`; preserves the per-lens read.
- `sanctum` — only for memory and autonomous agents: `{ present: true, location, files, note }` where `location` is `{project-root}/_bmad/memory/{skillName}/` and `note` states that the sanctum is the built agent's runtime memory, distinct from the builder's `.memlog.md` — never blur the two. Omit the block (or set `present: false`) for a stateless agent.
- `experience` — `journeys` as `{ name, steps }` for the main paths a user takes through the agent, and `headless` as one line on the agent's headless story.

## Schema (schema_version 2)

`findings.json` is one object:

```json
{
  "schema_version": 2,
  "subject": "<agent name or path analyzed>",
  "generated": "<ISO date>",
  "verdict": "<one-line overall assessment>",
  "grade": "excellent | good | fair | poor",
  "summary": "<2-3 sentence narrative>",
  "standards": {
    "canon": "<absolute path to this builder's references/prompt-quality-canon.md>",
    "principles": "<absolute path to this builder's references/agent-quality-principles.md>",
    "scripts": "<absolute path to this builder's references/script-standards.md>"
  },
  "agent_profile": { "name": "", "title": "", "icon": "", "agent_type": "", "mission": "" },
  "capabilities": [{ "name": "", "kind": "", "note": "" }],
  "detailed_analysis": { "leanness": "<lens verdict>", "architecture": "<lens verdict>" },
  "sanctum": { "present": true, "location": "", "files": [], "note": "" },
  "experience": { "journeys": [{ "name": "", "steps": "" }], "headless": "" },
  "themes": [
    {
      "title": "<root-cause name>",
      "root_cause": "<what is happening and why it matters>",
      "finding_ids": ["leanness-1", "determinism-2"],
      "action": "<one coherent fix for the whole theme>"
    }
  ],
  "strengths": ["<what works and should be preserved>"],
  "recommendations": [
    { "rank": 1, "action": "<what to do>", "resolves": ["leanness-1"] }
  ],
  "findings": [
    {
      "id": "<lens>-<n>",
      "lens": "leanness | architecture | determinism | customization | enhancement | agent-cohesion | sanctum-architecture",
      "severity": "critical | high | medium | low",
      "title": "<short>",
      "location": "<file:region>",
      "evidence": "<what was observed>",
      "recommendation": "<the fix>",
      "proposed_smallest": "<optional, leanness only>",
      "predicted_delta": "<optional, leanness only>"
    }
  ]
}
```

Rules:

- `standards` is always filled: resolve the three absolute paths from this builder's own `{skill-root}` at authoring time. The shell prepends them to every copied fix prompt, so the session that applies a fix holds the same bar that produced the findings.
- `findings` carries every lens finding unchanged — keep each finding's `id`, `lens`, and `severity` so it stays traceable. Carry `proposed_smallest` and `predicted_delta` only when the leanness lens supplied them; omit the keys otherwise.
- Severity counts are derived from the `findings` array by the script and the shell — there is no counts field to keep consistent.
- Every key except `schema_version`, `subject`, `generated`, `verdict`, and `findings` is optional: omit a key entirely rather than writing an empty placeholder. A clean pass is a real report — empty `findings`, a grade that reflects it, and a verdict saying the lenses passed.
- Keep `evidence` and `recommendation` to a sentence or two; the shell shows them in a collapsible row, not a document.

## Write and render

1. Write the object to `{run-folder}/findings.json`.
2. Render:

   ```bash
   python3 scripts/render_report.py {run-folder}/findings.json --shell assets/report-shell.html -o {run-folder}/agent-analysis-report.html --md {run-folder}/agent-analysis-report.md
   ```

   The script refuses bad JSON, a bad shape, or a placeholder subject — fix `findings.json` and re-run; never hand-edit the HTML. On success it prints one JSON line with the output paths and the severity counts to report.
3. Open the HTML for the user. The markdown twin is the archival artifact of the same data.

The shell fails loud: a malformed island shows the parse-error banner, an unfilled shell shows a placeholder banner, and an empty findings array with a real subject renders an explicit no-findings panel — never a blank page and never fabricated findings.
