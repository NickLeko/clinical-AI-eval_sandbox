# Reviewer Guide

## Who This Is For

This guide is for a hiring manager, PM interviewer, engineer, or healthcare AI stakeholder who wants to understand the repository quickly without reading every file in depth.

Read this file if you want the fastest review path through the repo and the most important takeaways.

## 3-Minute Review Path

1. Read `README.md`
- Understand what the project is, what it evaluates, what it does not claim, and where the main artifacts live.

2. Open `results/run_manifest.json`
- Confirm the exact provider / model / run backing the public artifact set.

3. Open `results/summary.md`
- See the benchmark snapshot and top-line interpretation guardrails.

3a. Optional: read `docs/results_interpretation.md`
- Use this if you want guardrails for interpreting PASS/WARN/FAIL, safety rates, and model comparisons.

4. Read `docs/failure_modes.md`
- Understand what kinds of failures the benchmark is designed to surface.

5. Read `docs/notable_failures.md`
- See the current status of flagged-case review for the published run.

6. Read `docs/maintenance_boundaries.md`
- Confirm which files are benchmark-defining and intentionally protected.

## What This Repo Demonstrates

The repository is strongest as a signal of:

- healthcare AI evaluation judgment
- safety-first benchmarking
- faithfulness and uncertainty awareness
- structured artifact design
- honest limitations and governance thinking

## What To Look At If You Want More Depth

- `docs/architecture.md` for the dataset -> prompt -> generation -> scoring -> reporting flow
- `docs/safety_case.md` for hazard framing and mitigation logic
- `src/metrics.py` for scoring and flag definitions
- `src/prompt_templates.py` for the structured response contract

## What This Repo Does Not Claim

This project does not claim:

- clinical validation
- production readiness
- regulatory approval
- clinician adjudication
- complete safety coverage

It is an evaluation sandbox and portfolio artifact, not a medical product.

## Benchmark Boundary Reminder

If you are reviewing maintenance quality, the benchmark-defining files are intentionally treated as protected. Documentation can be improved freely, but changes to dataset content, prompt behavior, scoring logic, safety flags, or reported artifacts should be treated as explicit evaluation revisions.

## Suggested Reviewer Takeaway

The main takeaway is not that any specific model is safe for healthcare use. The main takeaway is that even capable models can still trigger safety-relevant warnings or failures, and that a disciplined evaluation harness is necessary before deployment.
