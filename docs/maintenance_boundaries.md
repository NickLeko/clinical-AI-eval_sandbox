# Maintenance Boundaries For Evaluation-Sensitive Changes

This repository is maintained as both a software project and an evaluation artifact. That means some files should be treated as benchmark-defining assets rather than routine implementation details.

Read this file if you want to know which changes are safe documentation maintenance and which changes should be treated as explicit benchmark revisions.

## High-Sensitivity Zones

Casual edits to the following areas can silently change benchmark meaning:

- `dataset/clinical_questions.csv`
  - Defines case semantics, expected behavior, citation requirements, and forbidden actions.
- `src/prompt_templates.py`
  - Defines the exact response instructions and output structure used during generation.
- `src/generate_answers.py`
  - Controls prompt application, cache keys, provider/model metadata, and raw generation artifacts.
- `src/metrics.py`
  - Defines scoring behavior, safety flags, failure tags, and PASS/WARN/FAIL logic.
- `src/run_evaluation.py`
  - Controls how generations are merged with the dataset and translated into scored outputs.
- `results/`
  - Stores reported artifacts that represent benchmark outputs for this repo version.

## Protected Meanings

Do not change these accidentally:

- dataset semantics
- prompt behavior
- evaluation logic
- safety-flag behavior
- citation or faithfulness scoring behavior
- refusal-handling behavior
- reported results or benchmark claims
- provider/model comparison meaning
- artifact field meaning

## Low-Risk Maintenance Examples

Safe maintenance usually includes:

- README clarity improvements
- doc navigation and cross-links
- formatting and information hierarchy fixes
- explicit scope and limitation notes
- reviewer guidance for interpreting artifacts

## Change Taxonomy

### Docs-only maintenance

This includes changes that improve readability without altering benchmark meaning.

Examples:

- README restructuring
- documentation cross-links
- reviewer guides
- artifact-reading guidance
- wording cleanups that preserve claims exactly

### Benchmark revision

This includes any change that alters how the benchmark works or what it means.

Examples:

- dataset edits
- prompt changes
- scoring or flag logic changes
- changes to evaluation thresholds or summary calculations
- changes that affect provider or model comparison meaning

These changes should be called out explicitly as evaluation revisions.

### Result refresh

This includes rerunning or replacing generated benchmark artifacts, even if the code and dataset are unchanged.

Examples:

- regenerating `results/raw_generations.jsonl`
- replacing `results/evaluation_output.csv`
- replacing `results/flagged_cases.jsonl`
- replacing `results/summary.md`

These changes should be called out explicitly as result refreshes so reviewers can distinguish refreshed artifacts from unchanged reported outputs.

## Changes That Require Explicit Intent

The following should be treated as benchmark revisions, not routine cleanup:

- changing dataset rows or labels
- changing prompt wording or required output sections
- changing scoring thresholds, heuristics, or flag definitions
- changing summary calculations or benchmark tables
- regenerating or replacing `results/` artifacts

If one of these changes is needed, it should be called out explicitly in the PR or commit message as an evaluation revision.

If results are regenerated without changing benchmark logic, that should still be called out explicitly as a result refresh.

## Maintenance Rule Used In This Pass

This maintenance pass is documentation-only. It does not modify:

- dataset content
- prompt template behavior
- evaluation logic
- safety flags
- benchmark artifacts
- reported results

That boundary is intentional to preserve reproducibility and reviewer trust.
