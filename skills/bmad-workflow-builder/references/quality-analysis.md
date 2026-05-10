# Quality Analysis

Communicate with user in `{communication_language}`. Write report content in `{document_output_language}`.

You orchestrate quality analysis on a BMad workflow or skill. Deterministic checks run as scripts (zero tokens). Judgment-based analysis runs as parallel LLM scanner subagents. A report creator synthesizes everything into a unified, theme-based report.

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

### Step 3: Synthesize Report

After all scanners complete, spawn a subagent with `references/report-quality-scan-creator.md`. Provide `{skill-path}` and `{quality-report-dir}`. The report creator reads everything, synthesizes themes, and writes `quality-report.md` and `report-data.json` to `{quality-report-dir}`.

### Step 4: Generate HTML Report

```bash
python3 scripts/generate-html-report.py {quality-report-dir} --open
```

## Present to User

**IF `{headless_mode}=true`:**

Read `report-data.json` and output:

```json
{
  "headless_mode": true,
  "scan_completed": true,
  "report_file": "{path}/quality-report.md",
  "html_report": "{path}/quality-report.html",
  "data_file": "{path}/report-data.json",
  "warnings": [],
  "grade": "Excellent|Good|Fair|Poor",
  "opportunities": 0,
  "broken": 0
}
```

**IF interactive:**

Read `report-data.json` and present:

1. Grade and narrative — the 2-3 sentence synthesis
2. Broken items (if any) — critical/high issues prominently
3. Top opportunities — theme names with finding counts and impact
4. Reports — "Full report: quality-report.md" and "Interactive HTML opened in browser"
5. Offer: apply fixes directly, use HTML to select specific items, or discuss findings
