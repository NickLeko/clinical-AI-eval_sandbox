# Results Interpretation Guide

This document explains how to interpret the benchmark outputs responsibly.

Read this file if you want guardrails for understanding PASS / WARN / FAIL, safety rates, and model comparisons without overstating what the benchmark proves.

## What The Results Represent

The reported results represent behavior on one explicit published provider / model / run under this repository's fixed evaluation dataset, prompt structure, scoring heuristics, and artifact pipeline.

They are best understood as:

- benchmark-specific observations
- safety-oriented screening signals
- evidence for reviewer discussion

They are not universal claims about a model's safety or clinical reliability.

## How To Read PASS / WARN / FAIL

- `PASS` means the response avoided the current hard-failure and warning conditions in this benchmark.
- `WARN` means the response triggered a notable concern under the heuristic scoring rules.
- `FAIL` means the response triggered a hard-failure condition, such as an unsafe recommendation.

These grades are useful for triage and comparison within this benchmark. They are not equivalent to clinician adjudication or deployment approval.

## How To Read Safety Rates

Rates such as unsafe recommendation rate, hallucination suspicion rate, and refusal failure rate should be read as benchmark-specific screening rates.

They help answer questions like:

- which failure patterns appeared in this evaluation set
- whether certain models showed more concerning patterns on these cases
- whether a future revision appears safer or riskier on the same benchmark

They do not answer questions like:

- whether a model is generally safe in healthcare
- whether a model should be deployed clinically
- whether a model is safer in every context

## How To Read Model Comparisons

Model comparisons in this repo are meaningful only within the fixed benchmark setup:

- same dataset
- same prompt structure
- same evaluation heuristics
- same artifact definitions

That means the comparisons are useful for internal benchmark interpretation, but they should not be generalized too broadly.

## Important Limitation For v1

The current evaluator includes a negation-aware check for forbidden actions and direct clinical action language, which removes the earlier false-positive pattern where answers like `"do not prescribe amoxicillin"` could be flagged as unsafe recommendations.

This matters because:

- the current published unsafe and hallucination rates should not inherit that earlier false-positive pattern
- historical cached raw generations under `results/cache/` may still reflect exploratory runs produced before the public artifact set was cleaned up
- the evaluator is still heuristic and should not be mistaken for clinician adjudication

Even with that fix, the benchmark remains a screening artifact rather than a clinical validation method.

## Responsible Takeaways

Reasonable takeaways include:

- even capable models can still trigger safety-relevant warnings or failures
- safety-oriented evaluation is necessary before healthcare deployment
- benchmark artifacts should be reviewable and auditable
- limitations should be documented honestly

Unreasonable takeaways include:

- a passing model is clinically safe
- a failing model is categorically unusable
- these rates transfer directly to real-world deployment settings

## Related Docs

- `README.md` for the overall benchmark framing
- `docs/artifacts_guide.md` for file-by-file output meaning
- `docs/failure_modes.md` for failure taxonomy and the documented v1 limitation
- `docs/safety_case.md` for safety framing and non-claims
