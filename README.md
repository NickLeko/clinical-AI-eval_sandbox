# Clinical AI Evaluation Sandbox

A lightweight, safety-oriented evaluation harness for testing how LLMs behave in clinical decision-support scenarios before deployment.

This repository is meant to signal evaluation judgment, safety-first thinking, and disciplined benchmark communication. It is not a medical device, not a clinical product, and not for patient care.

Read this file if you want the fastest overview of what the project is, what it evaluates, what artifacts it produces, and what it does not claim.

## What This Project Is

This project simulates a pre-deployment healthcare AI evaluation workflow:

- run a fixed clinical evaluation dataset
- generate structured model responses from a fixed prompt template
- score outputs with safety- and faithfulness-oriented heuristics
- surface flagged cases for human review
- summarize benchmark artifacts for reviewer inspection

The goal is not to build a medical model. The goal is to build a credible evaluation sandbox that shows how a healthcare AI team might risk-test an LLM before workflow integration.

## Why It Matters

Clinical AI evaluation cannot rely on accuracy alone. This sandbox focuses on signals that matter in healthcare settings:

- faithfulness to provided context
- citation validity
- uncertainty and refusal behavior
- unsafe recommendation detection
- reviewer-friendly failure analysis

The repo is intentionally small, auditable, and portfolio-friendly rather than production-complete.

## What It Evaluates

The benchmark uses structured clinical scenarios and checks whether a model:

- answers from the provided context instead of inventing facts
- cites the allowed context anchors
- expresses uncertainty or refuses when evidence is insufficient
- avoids forbidden or unsafe actions
- follows a response format that is easy to inspect and score

## What It Does Not Claim

This repository does not claim:

- clinical validity
- clinician-grade adjudication
- regulatory readiness
- complete safety coverage
- real-world deployment approval

Faithfulness and safety checks are heuristic by design. Results should be interpreted as a controlled evaluation artifact, not as proof that a model is clinically safe.

## 2-Minute Repo Map

```text
clinical-AI-eval_sandbox/
├── dataset/
│   └── clinical_questions.csv      # Fixed evaluation cases
├── src/
│   ├── prompt_templates.py         # Prompt template used for all cases
│   ├── llm_clients.py              # Provider adapters
│   ├── generate_answers.py         # Runs model generation and caches outputs
│   ├── metrics.py                  # Scoring and safety flags
│   ├── run_evaluation.py           # Applies metrics to generations
│   └── summarize_results.py        # Builds markdown summary
├── results/
│   ├── raw_generations.jsonl       # Raw prompts, answers, metadata
│   ├── evaluation_output.csv       # Scored case-level results
│   ├── flagged_cases.jsonl         # WARN/FAIL subset for review
│   └── summary.md                  # Human-readable run summary
├── docs/
│   ├── architecture.md             # System overview
│   ├── safety_case.md              # Safety framing and hazards
│   ├── failure_modes.md            # Failure taxonomy and known limitations
│   ├── notable_failures.md         # Representative cases
│   └── maintenance_boundaries.md   # Eval-sensitive change policy
├── requirements.txt
└── README.md
```

## Likely Reviewer Workflow

For a first pass, a reviewer can understand the project in this order:

1. Read this README for project scope, benchmark boundaries, and artifact map.
2. Open `results/summary.md` for the headline benchmark view.
3. Check `docs/failure_modes.md` and `docs/notable_failures.md` for safety interpretation.
4. Inspect `src/metrics.py`, `src/run_evaluation.py`, and `src/prompt_templates.py` if they want to audit the benchmark mechanics.

## Evaluation Pipeline

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

## Core Outputs

The main review artifacts are:

- `results/raw_generations.jsonl`: raw prompts, answers, and run metadata
- `results/evaluation_output.csv`: case-level metrics, flags, and PASS/WARN/FAIL grades
- `results/flagged_cases.jsonl`: subset for manual inspection of concerning outputs
- `results/summary.md`: compact benchmark report with rates, means, and worst cases

## Reported Benchmark Snapshot

The repository includes benchmark results for 4 models on the same 25-case dataset, yielding 100 evaluated outputs total.

| Model | Cases Evaluated | PASS | WARN | FAIL | Unsafe Recommendation Rate | Hallucination Rate | Refusal Failure Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| GPT-4o | 25 | 22 | 0 | 3 | 12% | 12% | 0% |
| GPT-4.1-mini | 25 | 22 | 1 | 2 | 8% | 8% | 4% |
| GPT-3.5-turbo | 25 | 23 | 0 | 2 | 8% | 8% | 0% |
| GPT-4.1-nano | 25 | 23 | 0 | 2 | 8% | 8% | 0% |

Key takeaway: stronger general capability did not eliminate unsafe or ungrounded clinical behavior. This is exactly why healthcare-oriented evaluation and failure review matter.

## Running The Project

This repo is set up to run through GitHub Actions rather than requiring local infrastructure.

### GitHub Actions flow

1. Add an `OPENAI_API_KEY` repository secret.
2. Open the Actions workflow for the clinical evaluation run.
3. Provide workflow inputs such as provider, model, max cases, and prompt version.
4. Let the workflow generate answers, score them, summarize results, and write artifacts into `results/`.

Expected workflow inputs:

| Input | Example | Description |
|---|---|---|
| `provider` | `openai` | LLM provider |
| `model` | `gpt-4.1-mini` | Model used for generation |
| `max_cases` | `25` | Maximum dataset rows to run |
| `prompt_version` | `v1` | Prompt label tracked in artifacts |

### Local script entry points

If a reviewer wants to inspect the mechanics, the main scripts are:

- `src/generate_answers.py`
- `src/run_evaluation.py`
- `src/summarize_results.py`

This maintenance pass does not change how those scripts behave.

## Documentation Guide

- `docs/architecture.md`: architecture, modules, and data flow
- `docs/artifacts_guide.md`: what each results artifact contains and how to read it
- `docs/results_interpretation.md`: how to interpret benchmark outputs and model comparisons responsibly
- `docs/safety_case.md`: safety framing, hazards, and mitigations
- `docs/failure_modes.md`: common failure categories plus known v1 limitations
- `docs/notable_failures.md`: representative flagged cases
- `docs/reviewer_guide.md`: quick walkthrough for interviewers and other reviewers
- `docs/maintenance_boundaries.md`: what should not be edited casually because it can change benchmark meaning

## Eval-Sensitive Areas

The following files are benchmark-sensitive and should be treated as protected unless a benchmark revision is explicitly intended:

- `dataset/clinical_questions.csv`
- `src/prompt_templates.py`
- `src/metrics.py`
- `src/run_evaluation.py`
- `src/generate_answers.py`
- `results/summary.md`
- `results/evaluation_output.csv`
- `results/flagged_cases.jsonl`
- `results/raw_generations.jsonl`

See `docs/maintenance_boundaries.md` for the maintenance policy used in this repo.

## Known Scope Boundaries

- The dataset is intentionally small and reviewable.
- Safety flags are heuristic and incomplete.
- Reported results are versioned artifacts, not universal model judgments.
- Human clinical review is outside the automated pipeline.
- A documented v1 unsafe-action limitation is intentionally preserved for benchmark reproducibility rather than silently corrected.

## Why This Repo Works As A Portfolio Artifact

It demonstrates:

- healthcare AI evaluation framing
- safety-aware benchmark design
- structured prompt and scoring discipline
- honest limitations and governance thinking
- reviewer-friendly artifact organization

## Disclaimer

This repository demonstrates evaluation methods for healthcare AI systems. It must not be used to provide medical advice, support patient care, or make clinical decisions.
