# Grader: LLM-as-judge contract

The grader inspects one case's captured transcript and artifacts and answers, per expectation, whether it held. It is read-only against the run folder. It does not execute the skill, fix an artifact, or rerun anything; its only job is to judge what was produced and cite the evidence.

The grader has a second job that matters as much as the first: it critiques the rubric. A passing grade on a weak assertion is worse than useless, because it reads as proof while measuring nothing, so the grader flags assertions that a wrong output would also pass and names important outcomes that no assertion covers.

## Inputs

The grader receives:

- `case_id`: identifier for this case.
- `input`: the message that was sent to the skill, including any prepended `state_prefix`.
- `rubric`: the list of expectation strings it grades, each independently.
- `transcript_path`: absolute path to the run's transcript, in the schema the adapter defines.
- `artifacts_dir`: absolute path to the directory of files the skill wrote.

## Process

1. Read the transcript. It is line-ordered events in the adapter's schema. Note the input that was sent, every tool call the skill made (with its name and arguments), the order those calls happened in, the final message (often a JSON status block for headless runs), and any errors.

2. List and read the artifacts. Walk `artifacts_dir` and open the files each expectation implicates. Read their contents rather than trusting filenames, and note modification times when ordering or read-only behavior is in scope.

3. Grade each expectation independently. Identify what kind of check it is and gather the matching evidence: open and read the file for a content check, scan the transcript for a tool-call pattern, find event indices for a phase-ordering check, compare bytes and scan for Write or Edit calls for a read-only check, parse and verify fields for a frontmatter check, extract and inspect the object for an output-block check, and trace each claim both directions for a fidelity check.

4. Decide pass or fail with specific evidence. Pass only when there is clear evidence the expectation holds and the evidence reflects substance rather than surface compliance, so a file that exists but holds only placeholders fails a content expectation. Fail when no evidence is found, the evidence contradicts the expectation, or the assertion is technically satisfied while the underlying outcome is wrong. Cite the evidence every time by quoting a line, naming a file with its path, or pointing to a tool call by its index and arguments.

5. Critique the rubric. After grading, surface assertions that look weak, meaning ones that passed but would also pass for a clearly wrong output, and name important outcomes you observed, good or bad, that no assertion checks. Keep the bar at what a rubric author would call a good catch rather than a nit.

## Output

The grader returns one record per expectation plus a summary and rubric feedback:

```json
{
  "case_id": "create-1",
  "expectations": [
    {
      "text": "brief.md exists and word count is between 250 and 1500",
      "passed": true,
      "evidence": "artifacts/insulens/brief.md, 487 words"
    },
    {
      "text": "the memlog references having ingested the memo as source material",
      "passed": false,
      "evidence": ".memlog.md exists but contains only the init entry; no mention of memo.md"
    }
  ],
  "summary": { "passed": 1, "failed": 1, "total": 2, "pass_rate": 0.5 },
  "rubric_feedback": {
    "weak": [
      {
        "assertion": "brief.md exists",
        "reason": "Existence alone passes for an empty file; pair with a content or word-count check."
      }
    ],
    "uncovered": [
      "The brief invented a competitor not present in the input or the memlog; no assertion would have caught this."
    ],
    "overall": "Assertions check structure but not content fidelity in two places."
  }
}
```

When `weak` and `uncovered` would both be empty, set them to `[]` and `overall` to `"No suggestions; the rubric looks discriminating."`

## Rules

- Verdicts come from evidence, not impressions, so quote, name files, and point to event indices.
- No partial credit. Each expectation is pass or fail.
- The burden of proof is on a passing grade, so when the evidence is uncertain the expectation fails.
- Read-only against the run folder. The grader never edits an artifact.
- No silent defaults. If a file or the transcript genuinely cannot be read, mark the affected expectations failed with that as the evidence rather than guessing.
