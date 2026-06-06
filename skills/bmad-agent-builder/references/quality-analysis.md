---
name: quality-analysis
description: The Analyze orchestrator for BMad agents. Runs the deterministic pre-pass, dispatches the quality lenses in parallel, merges their findings in-context, and hands one report-author the island it renders into the stable shell. No per-subagent files.
---

**Language:** Use `{communication_language}` for all output.

# Analyze: Quality Analysis for a BMad Agent

Personality is investment, not waste. You analyze an agent to find where its capability prompts, structure, and wiring can be leaner or sharper, and you never recommend that the agent's voice be flattened. A rich persona is the deliverable, so the lenses apply the leanness bar to capability prompts and to leaked structure, not to persona voice, communication-style examples, domain framing, design rationale, or theory-of-mind.

`{target-agent-path}` is the agent directory under analysis, a directory containing a `SKILL.md`. You orchestrate: the pre-pass classifies and counts, the lenses judge, and the report-author renders. You do not read the agent's raw files yourself, because the pre-pass and the lenses already do and your context is better spent merging their returns.

## Headless mode

If `{headless_mode}=true`, skip user interaction, take safe defaults, note any warning rather than asking, and emit the structured JSON described under Present. This is the builder's own headless mode and has nothing to do with a built autonomous agent's runtime Quiet Rebirth; the two share a flag name and nothing else.

## Pre-scan check

Confirm the agent is resolvable at `{target-agent-path}` and that a `SKILL.md` is present. In interactive mode, note any uncommitted changes in the agent tree so the user knows the report reflects the working copy; in headless mode record that as a warning and proceed. You do not commit, stage, or push anything.

## Run the deterministic pre-pass first

Run the pre-pass once, before any lens sees the agent, so every lens reads a compact classification and token picture instead of re-deriving it from raw text:

```bash
python3 scripts/prepass.py {target-agent-path}
```

It prints one JSON object on stdout, the pinned pre-pass shape:

```json
{
  "agent_type": "stateless | memory | autonomous",
  "is_memory_agent": true,
  "skill_md_tokens": 0,
  "files": [{ "path": "SKILL.md", "tokens": 0 }]
}
```

Hold that object. `agent_type` and `is_memory_agent` decide whether the conditional sanctum lens runs, and the token counts are the lengths the lenses reason about. Lengths come from tokens here, never line counts. The pre-pass reads the built agent's sanctum to classify it; it never reads the builder's `.memlog.md`, and neither do you.

## Dispatch the lenses in parallel

Hand each lens the pre-pass JSON and `{target-agent-path}`, and run them as parallel subagents. Each lens loads `references/agent-quality-principles.md` (which cedes the universal core to `references/prompt-quality-canon.md`), stays in its lane, and returns its findings to you in-context. No lens writes a file or a per-subagent analysis document.

Six base lenses run for every agent:

| Lens | File | Owns |
| --- | --- | --- |
| Leanness | `references/scan-leanness.md` | The three minimal-baseline tests applied to capability prompts and leaked structure, with the persona carve-out held explicit. The only lens that fills `proposed_smallest` and `predicted_delta`. |
| Architecture | `references/scan-architecture.md` | Frontmatter, topology, progressive disclosure, headless soundness, ordering, parallelization, read-avoidance. |
| Determinism | `references/scan-determinism.md` | The determinism test, the signal-verb scan, the script-opportunity categories, intelligence placement, and the transcript repeated-work signal. |
| Customization | `references/scan-customization.md` | The customize.toml surface, its abuse lenses branched by archetype, and confirmation it is the only config mechanism present. |
| Enhancement | `references/scan-enhancement.md` | Edge cases, experience gaps, delight, headless potential, facilitative patterns. |
| Agent cohesion | `references/scan-agent-cohesion.md` | Persona-capability alignment, gaps, redundancy, granularity, user-journey coherence. |

One conditional lens runs only when the pre-pass classified the agent as memory or autonomous:

| Lens | File | Runs when |
| --- | --- | --- |
| Sanctum architecture | `references/scan-sanctum-architecture.md` | `is_memory_agent` is `true`. Bootloader weight, sanctum templates, First Breath, CREED standing orders, the init script. Skipped entirely for a stateless agent. |

Read `is_memory_agent` from the pre-pass. If it is `true`, include the sanctum lens in the parallel dispatch so seven lenses run. If it is `false`, dispatch the six base lenses only and the report will carry no sanctum block.

Every lens returns the same JSON shape (schema_version 1):

```json
{
  "lens": "leanness | architecture | determinism | customization | enhancement | agent-cohesion | sanctum-architecture",
  "verdict": "<one line for this lens>",
  "findings": [
    {
      "id": "<lens>-<n>",
      "severity": "critical | high | medium | low",
      "location": "<file:region or file>",
      "evidence": "<what was observed>",
      "recommendation": "<the fix, including a cut where it applies>",
      "proposed_smallest": "<leanness only, else null>",
      "predicted_delta": "<leanness only, else null>"
    }
  ]
}
```

Only the leanness lens fills `proposed_smallest` and `predicted_delta`. Those two fields let you route a defend-against-absence finding to the eval-runner's variant mode for a real cut-or-keep verdict rather than a guess; that routing happens in the build flow, not here.

## Merge in-context, then build the island

Merge the lens returns into one findings list, keeping each finding's `id` so it stays traceable to the lens that raised it. Tally the severity counts across all findings for the summary. Do this in your own context; there is no `report-data.json` on disk and no extract-and-reassemble round-trip.

Build the one island the report-author will render, conforming to the pinned island schema (schema_version 1). It carries the merged findings plus the agent blocks:

- `agent_profile`: the portrait. `name`, `title`, `icon`, `agent_type` (straight from the pre-pass), and a one-line `mission`. Draw the name, title, and icon from the agent's `[agent]` metadata as the lenses reported it.
- `capabilities`: the dashboard, a list of `{ name, kind, note }` where `kind` is the capability form (prompt, script, multi-file, external skill) and `note` is one line on what it does. Built from what the architecture and agent-cohesion lenses observed.
- `detailed_analysis`: keyed by lens name, each value the lens's one-line `verdict`. This is an additive block the shell tolerates; it preserves the per-lens read for anyone inspecting the island.
- `sanctum`: conditional. Include it only when the agent is memory or autonomous, carrying `{ present: true, location, files, note }` where `location` is `{project-root}/_bmad/memory/{skillName}/`, `files` lists the sanctum templates present, and `note` states that the sanctum is the built agent's runtime memory, distinct from the builder's `.memlog.md`. Omit the block for a stateless agent, or set `present: false`, and the shell renders no sanctum panel.
- `experience`: `{ journeys, headless }`. `journeys` is a list of `{ name, steps }` capturing the main paths a user takes through the agent, and `headless` is one line on the agent's headless story (for a memory agent, whether a Quiet Rebirth path is wired; for stateless, that headless is not applicable).

The agent blocks are optional in the shell's normalize(), so a sparse island still renders. Populate every block you have signal for, and leave out only what genuinely does not apply.

## Hand off to the report-author

Invoke `references/report-author.md` as one subagent. Give it the merged island JSON you built, the subject (the agent name or `{target-agent-path}`), and the run folder to write into (beside the agent's `.memlog.md`, under a timestamped analysis directory). The report-author reads `assets/report-shell.html`, replaces the single `report-data` island with your JSON, and writes the output HTML. It renders what you hand it and invents nothing.

The shell parses its island in a loud try/catch and shows a visible banner if the JSON is malformed, never a blank page. An empty findings array renders an explicit no-findings panel, so a clean agent still produces a real report. Open the resulting HTML for the user.

## Present

**IF `{headless_mode}=true`:** emit

```json
{
  "headless_mode": true,
  "scan_completed": true,
  "agent_type": "stateless | memory | autonomous",
  "html_report": "{path}/agent-analysis-report.html",
  "summary": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "top_findings": ["<id>: <title>", "..."]
}
```

**IF interactive:** present the agent portrait (icon, name, title, type), the one-line verdict, the severity tally, the capability dashboard summary, and the top findings. Note that the persona was treated as investment and was not flagged as waste. Point to the HTML report path, say it opened in the browser, and offer to walk through findings, apply a fix, or route a leanness finding's `proposed_smallest` to a variant eval.
