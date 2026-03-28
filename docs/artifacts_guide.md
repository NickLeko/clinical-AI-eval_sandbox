# Artifacts Guide

This document explains what each benchmark artifact contains, how a reviewer should read it, and what each file does and does not imply.

Read this file if you want a file-by-file guide to the outputs under `results/`.

## Artifact Set

The main benchmark artifacts are:

- `results/raw_generations.jsonl`
- `results/evaluation_output.csv`
- `results/flagged_cases.jsonl`
- `results/summary.md`

These files serve different review purposes. They should be read together rather than as substitutes for one another.

## `results/raw_generations.jsonl`

What it contains:

- prompt text
- model answer text
- run metadata such as provider, model, prompt version, and timestamp
- raw provider response payload for debugging

Why it matters:

- supports auditability
- shows exactly what the model saw and returned
- helps reviewers inspect individual outputs in context

What it does not mean:

- it is not the scored benchmark by itself
- it does not tell you whether an output passed or failed without the evaluation layer

## `results/evaluation_output.csv`

What it contains:

- case identifiers and run metadata
- metric scores
- boolean safety flags
- failure tags
- overall PASS / WARN / FAIL grading

Why it matters:

- this is the main structured scoring table
- it enables case-level comparison across runs, prompts, or models
- it makes the heuristic evaluation logic inspectable in tabular form

What it does not mean:

- it is not a clinician-adjudicated judgment set
- it should not be read as proof of real-world clinical safety

## `results/flagged_cases.jsonl`

What it contains:

- WARN and FAIL cases only
- the associated question, context, answer text, and failure tags

Why it matters:

- gives reviewers a faster path to concerning outputs
- supports manual inspection and qualitative failure review

What it does not mean:

- it is not the full benchmark population
- absence from this file does not prove a model is safe

## `results/summary.md`

What it contains:

- total cases scored
- PASS / WARN / FAIL distribution
- safety signal rates
- mean metric scores
- failure tag counts
- a short worst-case table

Why it matters:

- provides the fastest top-level benchmark snapshot
- makes the repo easy to review in a few minutes

What it does not mean:

- it is a summary view, not the full evidence base
- it should be cross-checked with `evaluation_output.csv` and flagged examples when making interpretations

## Suggested Review Order

1. Start with `results/summary.md` for the high-level snapshot.
2. Open `results/flagged_cases.jsonl` for representative concerning cases.
3. Use `results/evaluation_output.csv` for structured detail and comparison.
4. Inspect `results/raw_generations.jsonl` when you want full prompt-and-answer auditability.

## Interpretation Guardrails

- Treat these artifacts as benchmark-specific outputs, not universal model judgments.
- Treat heuristic flags as signals for review, not as definitive clinical conclusions.
- Read the artifacts alongside `docs/results_interpretation.md` and `docs/maintenance_boundaries.md`.

## Related Docs

- `README.md` for the repo overview
- `docs/results_interpretation.md` for benchmark-reading guidance
- `docs/reviewer_guide.md` for a fast review path
- `docs/maintenance_boundaries.md` for protected artifact meaning
