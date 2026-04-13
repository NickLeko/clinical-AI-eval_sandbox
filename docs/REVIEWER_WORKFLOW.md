# Reviewer Workflow

Use this workflow to inspect one run without confusing canonical artifacts, derived views, and cache/history files.

## Artifact Trust Map

| Artifact | Use it for | Authoritative for | Not authoritative for |
|---|---|---|---|
| `results/run_manifest.json` | Confirm run identity and provenance before reading scores. | Provider, model, run ID, prompt version, run kind, benchmark status, dataset coverage, case order, cache/live generation provenance. | Case-level scoring, clinical meaning, or model safety. |
| `results/evaluation_output.csv` | Inspect the full scored case table. | Case-level metric values, boolean safety flags, failure tags, PASS/WARN/FAIL grades, run metadata per row. | Raw prompts/answers, clinician adjudication, or proof of clinical safety. |
| `results/flagged_cases.jsonl` | Review WARN/FAIL examples quickly. | The flagged subset plus question, provided context, gold key points, answer text, grade, and failure tags for those cases. | The full benchmark population, absence of risk in non-flagged cases, or aggregate rates. |
| `results/summary.md` | Get the fastest top-level snapshot. | Headline distribution, rates, means, failure tag counts, and worst-case table for the artifact set. | Detailed case evidence or replacement for `evaluation_output.csv` and flagged-case review. |
| `results/reviewer_report.html` | Use a browser-friendly local view of the manifest, distributions, tags, and flagged cases. | Nothing canonical; it is a derived convenience view generated from the three published artifacts. | Scoring logic, artifact meaning, or source-of-truth results. |
| `results/raw_generations.jsonl` | Audit the exact model inputs and outputs when needed. | Raw prompt text, answer text, provider response payload, and generation metadata for the published run. | Scored grades or aggregate benchmark interpretation. |

## Recommended Review Order

1. Start with `results/run_manifest.json`.
   Confirm `provider`, `model_id`, `run_id`, `prompt_version`, `benchmark_status`, and dataset coverage before trusting any other artifact.
2. Read `results/summary.md` if present.
   Use it for orientation only.
3. Open `results/flagged_cases.jsonl`.
   Inspect WARN/FAIL cases qualitatively, especially failure tags and answer text.
4. Use `results/evaluation_output.csv`.
   Cross-check full-population scores, flags, and grade distribution.
5. Generate `results/reviewer_report.html` if a browser view is useful.
   Treat it as a local reader for the same artifacts, not a new result.
6. Inspect `results/raw_generations.jsonl` only when you need full prompt/answer audit detail.

## Generate The Reviewer Report

The report is self-contained HTML and is ignored by git.

```bash
make reviewer-report
```

Equivalent direct command:

```bash
python src/build_reviewer_report.py --results-dir results --output results/reviewer_report.html
```

Open `results/reviewer_report.html` in a browser. The report validates manifest/evaluation run identity and overlapping fields between `evaluation_output.csv` and `flagged_cases.jsonl` before rendering.

## Common Mistakes

- Do not treat PASS as proof that a model is clinically safe.
- Do not treat WARN/FAIL as clinician adjudication; they are heuristic review signals.
- Do not use `flagged_cases.jsonl` as the denominator for rates; use `evaluation_output.csv`.
- Do not treat `reviewer_report.html` as canonical. Regenerate it from artifacts when needed.
- Do not compare sandbox, candidate, and published runs without checking `run_manifest.json`.
- Do not treat `results/cache/raw_generations_cache.jsonl` as the published benchmark set.
