# Clinical AI Evaluation Sandbox Architecture

## Overview

The Clinical AI Evaluation Sandbox simulates how a healthcare organization might evaluate a Large Language Model (LLM) before integrating it into clinical decision-support workflows.

It evaluates model responses across safety-relevant dimensions:

- Faithfulness to provided clinical context
- Citation accuracy
- Uncertainty calibration
- Clinical safety risks

This framework is intentionally lightweight and designed to run as an automated evaluation pipeline.

---

## System Architecture

### Pipeline stages

1. Dataset
2. Prompt construction
3. LLM generation
4. Evaluation
5. Result storage
6. Summary reporting

### Data flow

Dataset
→ Prompt construction
→ LLM generation
→ Evaluation + safety flags
→ Results (CSV/JSONL)
→ Summary report (Markdown)

---

## Module Breakdown

### 1) Dataset layer

Location: `dataset/clinical_questions.csv`

The dataset contains structured clinical evaluation cases designed to probe model behavior under different clinical risk scenarios.

Each row may include:

- `case_id`: unique identifier
- `category`: scenario type (ICU triage, meds, guideline, coding, etc.)
- `risk_level`: low / medium / high
- `question`: clinical decision-support question
- `provided_context`: evidence snippet the model must use
- `expected_behavior`: `answer` / `uncertain` / `refuse`
- `required_citations`: anchors that must appear (pipe-separated)
- `forbidden_actions`: unsafe actions to detect (pipe-separated)
- `gold_key_points`: optional checklist (pipe-separated)
- `notes`: optional

Purpose: a small “golden” set that is stable, reviewable, and suitable for regression testing.

---

### 2) Prompt construction layer

Location: `src/prompt_templates.py`

Prompts enforce a strict response format so automated evaluation can parse reliably.

Required response sections:

- Recommendation
- Rationale (bullets with citations)
- Uncertainty & Escalation
- Do-not-do

Design intent:

- Reduce ambiguity in outputs
- Make safety and uncertainty explicit
- Make citations machine-checkable

---

### 3) Generation layer

Location: `src/generate_answers.py`

Responsibilities:

- Load the evaluation dataset
- Construct prompts from `question` + `provided_context`
- Call an LLM provider via an adapter interface
- Write raw generations with metadata
- Cache by prompt hash to avoid repeated API calls

Primary output: `results/raw_generations.jsonl`

Why JSONL: supports multiple runs/models and is easy to diff and audit.

---

### 4) Evaluation layer

Locations:

- `src/metrics.py`
- `src/run_evaluation.py`

This layer computes metric scores and applies safety flags.

Metric families (v1):

- Format compliance  
  Checks that required sections exist.

- Citation validity  
  Detects fabricated citation anchors and missing citations.

- Required citation coverage  
  Confirms required anchors appear for certain cases.

- Uncertainty alignment  
  Ensures the model refuses or hedges when expected, and avoids action language in refusal-required cases.

- Faithfulness proxy  
  Conservative heuristic using citation presence + lexical overlap + penalties for action-heavy, low-overlap responses.

Safety flags (deployment-gate style):

- Unsafe recommendation detected (forbidden action appears)
- Bogus citation detected (citation anchors outside allowed range)
- Refusal failure (expected refuse/uncertain but gives confident action)

Primary output: `results/evaluation_output.csv`  
Flagged subset: `results/flagged_cases.jsonl`

---

### 5) Reporting layer

Location: `src/summarize_results.py`

Creates a human-readable report for quick review.

Primary output: `results/summary.md`

Includes:

- PASS / WARN / FAIL distribution
- Mean metric scores
- Failure tag counts
- Worst performing cases

---

## Evaluation Philosophy

This sandbox is designed around healthcare risk thinking, not just accuracy.

Key principles:

- Prefer safe refusals over confident invention
- Require evidence-backed reasoning (citations)
- Treat unsafe recommendations as hard failures
- Surface failure patterns for human review

---

## Deployment Model (No Local Runtime)

The pipeline is intended to run via GitHub Actions.

High-level workflow:

- Install dependencies
- Generate answers (LLM calls)
- Run evaluation
- Generate summary report
- Commit results back to the repo

This enables reproducible evaluation without local infrastructure.

---

## Limitations

This sandbox is not clinical validation.

Known limitations:

- Faithfulness is a heuristic proxy (not full entailment verification)
- Safety detection is pattern-based and incomplete by design
- No clinician adjudication is included in v1
- Context snippets are simplified and not exhaustive

This project should be interpreted as an evaluation prototype and portfolio artifact, not a regulated system.

---

## Future Improvements

High-ROI extensions:

- Multi-model benchmarking
- Add clinician adjudication rubric for flagged cases
- Add retrieval stress-tests (context injection and irrelevant context)
- Add a simple dashboard that reads `results/evaluation_output.csv`
- Add regression gates (block merges if FAIL rate increases)

---

## Summary

The Clinical AI Evaluation Sandbox demonstrates a realistic pre-deployment evaluation harness for healthcare LLM decision support.

It shows:

- How to design a golden clinical evaluation dataset
- How to enforce structured responses for scoring
- How to implement safety flags and quality gates
- How to run evaluation in CI and publish auditable artifacts
