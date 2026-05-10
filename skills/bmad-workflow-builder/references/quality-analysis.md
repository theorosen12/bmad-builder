# Quality Analysis

Communicate with user in `{communication_language}`. Write report content in `{document_output_language}`.

You orchestrate quality analysis on a BMad workflow or skill. The pipeline is optimized for speed and completeness:

1. **Deterministic checks** (scripts) — zero tokens, instant
2. **LLM scanners** (parallel subagents) — judgment-based analysis against `skill-quality-principles.md`
3. **Fast JSON extraction** (deterministic script) — lossless capture of all scanner findings (~10 seconds, no LLM)
4. **HTML generation** — interactive, auto-opening report from JSON (no wait for synthesis)
5. **Optional markdown synthesis** (LLM subagent, background) — thematic analysis and archival markdown

The scanners verify against `references/skill-quality-principles.md` — the same file the build process loads at create/edit time. Findings cite the principle that's being violated rather than restating it.

## Your Role: Coordination, Not File Reading

**Do not read the target skill's files yourself.** Scripts and subagents do all analysis. You orchestrate: run deterministic scripts and pre-pass extractors, spawn LLM scanner subagents in parallel, hand off to the report creator for synthesis.

## Headless Mode

If `{headless_mode}=true`, skip user interaction, use safe defaults, note any warnings, and output structured JSON as specified in the Present Findings section.

## Pre-Scan Checks

Check for uncommitted changes. In headless mode, note warnings and proceed. In interactive mode, inform the user, confirm before proceeding, and confirm the workflow is currently functioning.

## Analysis Principles

**Effectiveness over efficiency.** The analysis may suggest leaner phrasing, but if the current phrasing captures the right guidance, it should be kept. The report presents opportunities — the user applies judgment.

## Scanners

### Lint Scripts (Deterministic — Run First)

Run instantly, cost zero tokens, produce structured JSON:

| #  | Script                           | Focus                                   | Output File                |
| -- | -------------------------------- | --------------------------------------- | -------------------------- |
| S1 | `scripts/scan-path-standards.py` | Path conventions                        | `path-standards-temp.json` |
| S2 | `scripts/scan-scripts.py`        | Script portability, PEP 723, unit tests | `scripts-temp.json`        |

### Pre-Pass Scripts (Feed LLM Scanners)

Extract metrics so LLM scanners work from compact data instead of raw files:

| #  | Script                                  | Feeds                  | Output File                       |
| -- | --------------------------------------- | ---------------------- | --------------------------------- |
| P1 | `scripts/prepass-workflow-integrity.py` | architecture scanner   | `workflow-integrity-prepass.json` |
| P2 | `scripts/prepass-prompt-metrics.py`     | architecture scanner   | `prompt-metrics-prepass.json`     |
| P3 | `scripts/prepass-execution-deps.py`     | determinism scanner    | `execution-deps-prepass.json`     |

### LLM Scanners (Judgment-Based — Run After Scripts)

Each scanner loads `references/skill-quality-principles.md` and writes a free-form analysis document:

| #  | Scanner                              | Focus                                                                          | Pre-Pass | Output File                  |
| -- | ------------------------------------ | ------------------------------------------------------------------------------ | -------- | ---------------------------- |
| L1 | `quality-scan-architecture.md`       | Structural integrity, prose craft, cohesion (was: integrity + craft + cohesion)| Yes (P1, P2) | `architecture-analysis.md`   |
| L2 | `quality-scan-determinism.md`        | Intelligence placement, parallelization, subagent delegation, script opportunities (was: execution-efficiency + script-opportunities) | Yes (P3) | `determinism-analysis.md`    |
| L3 | `quality-scan-customization.md`      | customize.toml opportunities and abuse                                         | No       | `customization-analysis.md`  |
| L4 | `quality-scan-enhancement.md`        | Edge cases, UX gaps, headless potential, facilitative patterns                 | No       | `enhancement-analysis.md`    |

## Execution

Bind `{quality-report-dir} = {skill-path}/.analysis/{date-time-stamp}/` and create the directory. Use this single name in every script invocation and subagent prompt below. Quality analyses live at the skill's own root, as a peer of `.decision-log.md` and `SKILL.md` — the audit trail travels with the skill.

### Step 1: Run All Scripts (Parallel)

```bash
python3 scripts/scan-path-standards.py {skill-path} -o {quality-report-dir}/path-standards-temp.json
python3 scripts/scan-scripts.py {skill-path} -o {quality-report-dir}/scripts-temp.json
uv run scripts/prepass-workflow-integrity.py {skill-path} -o {quality-report-dir}/workflow-integrity-prepass.json
python3 scripts/prepass-prompt-metrics.py {skill-path} -o {quality-report-dir}/prompt-metrics-prepass.json
uv run scripts/prepass-execution-deps.py {skill-path} -o {quality-report-dir}/execution-deps-prepass.json
```

### Step 2: Spawn LLM Scanners (Parallel)

After scripts complete, spawn all four LLM scanners as parallel subagents.

Each subagent receives:
- Scanner file to load
- Skill path: `{skill-path}`
- Output directory: `{quality-report-dir}`
- Pre-pass file paths (L1: P1+P2; L2: P3)

The subagent loads its scanner file (which loads the principles file), analyzes the skill, writes its analysis to `{quality-report-dir}`, and returns the filename.

### Step 3: Extract Report JSON (Fast, Deterministic)

After all scanners complete, extract structured data from analysis files into `report-data.json`. This is fast (<10s) and captures all scanner output without lossy synthesis:

```bash
python3 scripts/extract-report-json.py {skill-path} {quality-report-dir} -o {quality-report-dir}/report-data.json
```

This extracts:
- Assessment and findings from all 4 analysis files (architecture, determinism, customization, enhancement)
- All user journey archetypes, bright spots, friction points from enhancement
- Headless/automation potential from enhancement
- Prepass metrics from JSON files
- Complete, lossless `report-data.json` suitable for HTML generation

### Step 4: Generate & Open HTML Report

Generate the interactive HTML report from the JSON data (no wait for markdown):

```bash
python3 scripts/generate-html-report.py {quality-report-dir} --open
```

The HTML report is now interactive and auto-opens. No blocking on markdown synthesis.

### Step 5: Create Markdown Report (Optional, Background)

After HTML is generated, optionally spawn a background task with `references/report-quality-scan-creator.md` to synthesize markdown report. This is asynchronous; the user has their HTML. The report creator provides:
- Thematic synthesis (finds root-cause clusters across scanners)
- Markdown report with "What's Broken", "Opportunities", "Strengths", "Recommendations"
- Grade and narrative assessment

If synthesis time is a concern, this step can be omitted; the JSON + HTML are the primary deliverables. The markdown is archival.

### Step 6: Log the Run

Append a session heading to `{skill-path}/.decision-log.md` (create the file if absent). Cite the timestamped folder so the skill's history points to this run:

```markdown
## YYYY-MM-DD — Quality analysis

Grade: <grade from HTML>. Report: `.analysis/<timestamp>/quality-report.html`. Markdown: `.analysis/<timestamp>/quality-report.md` (if generated).
```

## Present to User

**Headless** (`{headless_mode}=true`): emit JSON only.

```json
{
  "status": "complete",
  "intent": "analyze",
  "skill": "{skill-path}",
  "decision_log": "{skill-path}/.decision-log.md",
  "report": "{quality-report-dir}/quality-report.md"
}
```

Blocked (scanner failure, missing required input, etc.): replace `"complete"` with `"blocked"` and add `"reason": "<one-line cause>"`. The log + any partial report carry the detail.

**Interactive:** read `report-data.json` and present grade + 2-3 sentence narrative, broken items if any, top opportunities by theme, paths to the full report and HTML. Offer to apply fixes, walk findings, or discuss.
