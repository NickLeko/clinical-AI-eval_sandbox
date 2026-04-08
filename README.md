# Clinical AI Evaluation Sandbox

A lightweight, safety-oriented evaluation harness for testing how LLMs behave in clinical decision-support scenarios before deployment.

This repository is meant to signal evaluation judgment, safety-first thinking, and disciplined benchmark communication. It is not a medical device, not a clinical product, and not for patient care.

Read this file if you want the fastest overview of what the project is, what it evaluates, what artifacts it produces, and what it does not claim.

The checked-in public artifacts represent one explicit canonical published run:

- provider: `openai`
- model: `gpt-4o`
- run_id: `20260305_045410`
- cases scored: `25`

Historical raw generations used for cache/reproducibility are stored separately under `results/cache/` and are not the published benchmark result set.

The generation layer currently supports these providers:

- `openai`
- `anthropic`
- `gemini`
- `mock`

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
│   ├── raw_generations.jsonl       # One explicit published provider/model/run
│   ├── run_manifest.json           # Published run identity and provenance
│   ├── evaluation_output.csv       # Scored case-level results
│   ├── flagged_cases.jsonl         # WARN/FAIL subset for review
│   ├── summary.md                  # Human-readable run summary
│   └── cache/
│       └── raw_generations_cache.jsonl   # Reusable raw-generation cache/history store
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
-> results/raw_generations.jsonl + results/run_manifest.json
-> src/run_evaluation.py + src/metrics.py
-> results/evaluation_output.csv + results/flagged_cases.jsonl
-> src/summarize_results.py
-> results/summary.md
```

## Core Outputs

The main review artifacts are:

- `results/raw_generations.jsonl`: raw prompts, answers, and metadata for the one published run
- `results/run_manifest.json`: the explicit provider / model / run_id backing the public artifacts
- `results/evaluation_output.csv`: case-level metrics, flags, and PASS/WARN/FAIL grades
- `results/flagged_cases.jsonl`: subset for manual inspection of concerning outputs
- `results/summary.md`: compact benchmark report with rates, means, and worst cases
- `results/cache/raw_generations_cache.jsonl`: reusable raw-generation cache/history store that is not itself the public benchmark set

## Current Published Run

The checked-in benchmark artifacts currently publish one explicit run:

- provider: `openai`
- model: `gpt-4o`
- run_id: `20260305_045410`
- dataset rows scored: `25`

Use `results/run_manifest.json` and `results/summary.md` together when reviewing the public benchmark set.

Important guardrail: a fully passing run on this heuristic benchmark is not evidence of clinical safety or deployment readiness.
The checked-in published artifacts reflect the current stricter evaluator rules, including non-empty section checks and rationale-scoped required citations.

## Running The Project

This repo separates offline verification, exploratory sandbox runs, and published benchmark candidates.

### Offline verification

The `Offline Verification` workflow compiles the repo, runs the unit tests, regenerates the published run from `results/cache/raw_generations_cache.jsonl`, and checks that the public artifacts reproduce exactly.

### Quick local verification

For a fast local health check before reviewing deeper:

```bash
pytest -q
python -m py_compile src/*.py tests/*.py
```

### Sandbox runs

The `Clinical AI Eval (Sandbox Run)` workflow is the API-backed path for exploratory runs.

Use it for:

- partial-dataset smoke tests
- prompt iteration checks
- provider comparisons
- `mock`-provider validation runs

Sandbox runs write to `sandbox_results/` inside the workflow and upload artifacts for review. They do not overwrite `results/`.

### Published benchmark candidate

The `Clinical AI Eval (Published Benchmark Candidate)` workflow is the guarded path for generating a full-dataset benchmark candidate for manual review.

It:

- forces the full dataset
- rejects the `mock` provider
- runs compile + unit-test checks first
- generates a live run, then rebuilds the candidate artifact set from cache
- verifies exact reproducibility before uploading the candidate artifacts

Published candidates are uploaded for manual review rather than pushed directly back to the repo.

Expected workflow inputs:

| Input | Example | Description |
|---|---|---|
| `model` | `gpt-4o` | Model used for generation |
| `prompt_version` | `v1` | Prompt label tracked in artifacts |
| `run_id` | `20260330_candidate` | Explicit benchmark-candidate run identifier |

### Local script entry points

If a reviewer wants to inspect the mechanics, the main scripts are:

- `src/generate_answers.py`
- `src/run_evaluation.py`
- `src/summarize_results.py`

`src/generate_answers.py` supports `--run-kind sandbox`, `--run-kind candidate`, and `--run-kind published`.
Use `sandbox` for exploratory or partial runs, `candidate` for full-dataset review artifacts, and `published` only for the checked-in canonical benchmark set and offline reproducibility.

Supported generation providers for `src/generate_answers.py`:

- `openai` using `OPENAI_API_KEY`
- `anthropic` using `ANTHROPIC_API_KEY`
- `gemini` using `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- `mock` for deterministic pipeline validation without API access

The multi-provider support above exists at the generation-script layer. The checked-in GitHub Actions workflows currently wire `openai` for API-backed runs and `mock` for pipeline validation; using `anthropic` or `gemini` in CI would require extending workflow secrets and inputs.

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
- `results/run_manifest.json`
- `results/summary.md`
- `results/evaluation_output.csv`
- `results/flagged_cases.jsonl`
- `results/raw_generations.jsonl`

See `docs/maintenance_boundaries.md` for the maintenance policy used in this repo.

## Known Scope Boundaries

- The dataset is intentionally small and reviewable.
- Safety flags are heuristic and incomplete.
- Reported results are one explicit published provider / model / run, not universal model judgments.
- Human clinical review is outside the automated pipeline.
- Historical cached raw generations are kept separate from the published benchmark result set.

## Why This Repo Works As A Portfolio Artifact

It demonstrates:

- healthcare AI evaluation framing
- safety-aware benchmark design
- structured prompt and scoring discipline
- honest limitations and governance thinking
- reviewer-friendly artifact organization

## Disclaimer

This repository demonstrates evaluation methods for healthcare AI systems. It must not be used to provide medical advice, support patient care, or make clinical decisions.
