# Clinical AI Evaluation Sandbox Architecture

## Purpose

This document explains how the Clinical AI Evaluation Sandbox is structured and how data moves through the evaluation pipeline.

It is an explanatory document, not a benchmark-defining artifact. For maintenance boundaries, see `docs/maintenance_boundaries.md`.

Read this file if you want the system map: dataset, prompt, generation, evaluation, reporting, and where each artifact comes from.

## At A Glance

The sandbox simulates how a healthcare organization might evaluate an LLM before integrating it into clinical decision-support workflows.

It focuses on:

- faithfulness to provided clinical context
- citation accuracy
- uncertainty calibration
- clinical safety risks

The system is intentionally lightweight and organized around a simple automated evaluation pipeline.

## Pipeline Overview

### Stages

1. Dataset
2. Prompt construction
3. LLM generation
4. Evaluation
5. Result storage
6. Summary reporting

### Data flow

```text
dataset/clinical_questions.csv
-> src/prompt_templates.py
-> src/generate_answers.py
-> results/raw_generations.jsonl
-> src/run_evaluation.py + src/metrics.py
-> results/evaluation_output.csv + results/flagged_cases.jsonl
-> src/summarize_results.py
-> results/summary.md
```

## Module Breakdown

### 1. Dataset layer

Location: `dataset/clinical_questions.csv`

The dataset contains structured clinical evaluation cases designed to probe model behavior under different clinical risk scenarios.

Each row may include:

- `case_id`: unique identifier
- `category`: scenario type such as ICU triage, medication, guideline, or diagnosis
- `risk_level`: low / medium / high
- `question`: clinical decision-support question
- `provided_context`: evidence snippet the model must use
- `expected_behavior`: `answer` / `uncertain` / `refuse`
- `required_citations`: anchors that must appear, pipe-separated
- `forbidden_actions`: unsafe actions to detect, pipe-separated
- `gold_key_points`: optional checklist, pipe-separated
- `notes`: optional

Purpose: a small golden set that is stable, reviewable, and suitable for regression testing.

### 2. Prompt construction layer

Location: `src/prompt_templates.py`

Prompts enforce a strict response format so automated evaluation can parse reliably.

Required response sections:

- Recommendation
- Rationale
- Uncertainty & Escalation
- Do-not-do

Design intent:

- reduce ambiguity in outputs
- make safety and uncertainty explicit
- make citations machine-checkable

### 3. Generation layer

Location: `src/generate_answers.py`

Responsibilities:

- load the evaluation dataset
- construct prompts from `question` and `provided_context`
- call an LLM provider through an adapter interface
- write raw generations with metadata
- cache by prompt hash to avoid repeated API calls

Primary output: `results/raw_generations.jsonl`

Why JSONL: it supports multiple runs and models and is straightforward to diff and audit.

### 4. Evaluation layer

Locations:

- `src/metrics.py`
- `src/run_evaluation.py`

This layer computes metric scores and applies safety flags.

Metric families in v1:

- Format compliance: checks that required sections exist
- Citation validity: detects fabricated citation anchors and missing citations
- Required citation coverage: confirms required anchors appear for certain cases
- Uncertainty alignment: ensures the model refuses or hedges when expected and avoids action language in refusal-required cases
- Faithfulness proxy: conservative heuristic using citation presence, lexical overlap, and penalties for action-heavy low-overlap responses

Safety flags:

- unsafe recommendation detected
- bogus citation detected
- refusal failure

Primary output: `results/evaluation_output.csv`

Flagged subset: `results/flagged_cases.jsonl`

### 5. Reporting layer

Location: `src/summarize_results.py`

Creates a human-readable report for quick review.

Primary output: `results/summary.md`

Includes:

- PASS / WARN / FAIL distribution
- mean metric scores
- failure tag counts
- worst performing cases

## Benchmark-Defining vs Explanatory Files

These files define benchmark meaning and should not be edited casually:

- `dataset/clinical_questions.csv`
- `src/prompt_templates.py`
- `src/generate_answers.py`
- `src/metrics.py`
- `src/run_evaluation.py`
- `results/`

This document, by contrast, is explanatory. It should help reviewers understand the system without changing evaluation semantics.

## Evaluation Philosophy

This sandbox is designed around healthcare risk thinking, not accuracy alone.

Key principles:

- prefer safe refusals over confident invention
- require evidence-backed reasoning through citations
- treat unsafe recommendations as hard failures
- surface failure patterns for human review

## Deployment Model

The pipeline is intended to run via GitHub Actions.

High-level workflow:

- install dependencies
- generate answers with LLM calls
- run evaluation
- generate summary report
- commit results back to the repo

This enables reproducible evaluation without local infrastructure.

## Limitations

This sandbox is not clinical validation.

Known limitations:

- faithfulness is a heuristic proxy, not full entailment verification
- safety detection is pattern-based and incomplete by design
- no clinician adjudication is included in v1
- context snippets are simplified and not exhaustive

This project should be interpreted as an evaluation prototype and portfolio artifact, not a regulated system.

## Suggested Reading Order

- Start with `README.md` for project scope and artifact map.
- Read `docs/artifacts_guide.md` for artifact meanings and file-by-file review guidance.
- Read `docs/safety_case.md` for safety framing and non-claims.
- Read `docs/failure_modes.md` for failure taxonomy and the documented v1 limitation.
- Read `docs/notable_failures.md` for representative examples.
- Read `docs/maintenance_boundaries.md` for protected benchmark areas.
