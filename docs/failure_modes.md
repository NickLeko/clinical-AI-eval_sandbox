# Clinical AI Evaluation Sandbox Failure Mode Analysis

## Purpose

This document catalogs common failure patterns observed when evaluating Large Language Models on clinical decision-support tasks.

The goal is to identify systematic risks that could appear if an LLM were integrated into healthcare workflows.

Failures are identified using the automated evaluation pipeline and grouped into repeatable failure modes.

Read this file if you want to understand what kinds of safety-relevant failures the benchmark is designed to surface and how to interpret the historical limitation that was fixed in the current evaluator.

## How To Read This Document

- The categories below describe the kinds of behavior the evaluation is trying to surface.
- The historical negation-blind unsafe-action matcher is no longer part of the current published evaluator.
- This document explains failure interpretation; it does not change benchmark results.

## Failure Mode Categories

### 1. Hallucinated Clinical Facts

Description:
The model generates medical facts that are not supported by the provided context.

Examples:

- inventing contraindications
- inventing drug interactions
- inventing guideline recommendations
- inventing diagnostic criteria

Example pattern:
Model response references clinical facts that do not appear in the provided context snippet.

Risk:
Hallucinated information can lead to incorrect clinical reasoning or unsafe treatment recommendations.

Detection method:
The evaluation system uses a heuristic faithfulness check based on:

- citation presence
- lexical overlap with context
- action language without supporting evidence

Flag used:
`HALLUCINATED_FACT`

### 2. Unsupported Citations

Description:
The model cites references that do not exist in the provided context.

Example:
Context provides anchors `CTX1` and `CTX2`, but the model response cites `CTX3`.

Risk:
Fabricated citations can create a false impression of evidence-based reasoning.

Detection method:
Citation anchors are validated against the anchors actually present in the case context.

Flag used:
`UNSUPPORTED_CITATION`

### 3. Unsafe Clinical Recommendations

Description:
The model recommends actions that may be harmful or contraindicated.

Examples:

- prescribing NSAIDs for CKD stage 4
- ignoring severe allergic reactions
- recommending incorrect dosing

Risk:
Unsafe recommendations represent the most serious failure mode.

Detection method:
Dataset cases include forbidden actions. Evaluation scans responses for unsafe terms.

Flag used:
`UNSAFE_RECOMMENDATION`

### 4. Refusal Failure

Description:
The model provides an answer when the correct behavior should be refusal.

Example:
The context does not contain sufficient evidence but the model still provides treatment advice.

Risk:
Failure to refuse may cause clinicians to rely on unsupported information.

Detection method:
Evaluation compares response behavior against the `expected_behavior` field.

Flag used:
`REFUSAL_FAILURE`

### 5. Uncertainty Misalignment

Description:
The model denies or mishandles uncertainty when the dataset expects refusal or limitation-aware behavior.

Examples:

- saying there is no uncertainty when refusal is expected
- failing to acknowledge limited evidence
- using strong certainty markers despite insufficient context

Risk:
Poor uncertainty handling can make unsupported answers look more reliable than they are.

Detection method:
Evaluation compares the response against the `expected_behavior` field and emits a warning when refusal- or uncertainty-expected cases do not show enough limitation language.

Flag used:
`UNCERTAINTY_MISALIGNED`

### 6. Unsupported Specificity

Description:
The model adds disease-specific or clinically specific detail that does not appear in a sparse provided context.

Example:
The context says urgent evaluation is needed, but the response escalates to named conditions such as `"heart attack"` or `"meningitis"` that are not present in the source snippet.

Risk:
Added specificity can overstate what the context supports and make a grounded-looking answer sound more authoritative than the evidence warrants.

Detection method:
The current evaluator applies a narrow sparse-context heuristic that looks for unsupported disease-specific elaboration in recommendation, rationale, or escalation text.

Flag used:
`UNSUPPORTED_SPECIFICITY`

## Observed Failure Patterns

The evaluator is designed to surface several recurring risk patterns:

1. Models often hallucinate additional clinical facts when context is sparse.
2. Models frequently produce treatment recommendations even when refusal is expected.
3. Citation formatting may appear correct even when the cited evidence is incorrect.
4. Strong action verbs correlate with hallucinated recommendations.

These patterns highlight why automated safety checks are necessary.

## Historical Limitation Fixed In The Current Evaluator

### Naive unsafe action detection

An earlier version of the evaluator used naive substring matching for unsafe recommendation and forbidden action detection. That created false positives when a response correctly contraindicated an action, such as `"do not prescribe NSAIDs"`, because the substring matcher ignored the surrounding negation.

Current status:
The current published evaluator uses a tightly scoped negation-aware check for forbidden actions and action-language heuristics, so that specific false-positive pattern is no longer part of the public benchmark artifacts.

Interpretation note:
Historical cached raw generations under `results/cache/` include exploratory runs produced before the published artifact set was cleaned up. Those cache rows should not be treated as the current benchmark result set.

## Current Published Run Status

The checked-in published run currently has 3 WARN cases and 0 FAIL cases under the corrected evaluator.

That should be interpreted narrowly:

- it means the published run triggered 2 `UNSUPPORTED_SPECIFICITY` warnings and 1 `UNCERTAINTY_MISALIGNED` warning
- it does not mean the model is clinically safe
- future benchmark refreshes may surface new flagged cases as the evaluator or published run changes

## Why Failure Analysis Matters

Understanding failure modes allows teams to improve AI systems through:

- prompt design improvements
- dataset expansion
- guardrail development
- monitoring systems

Failure analysis also informs clinical governance processes for AI tools.

## Related Docs

- `README.md` for project scope, run flow, and artifact map
- `docs/architecture.md` for system structure
- `docs/results_interpretation.md` for how failure rates and grades should be read
- `docs/notable_failures.md` for representative example cases
- `docs/maintenance_boundaries.md` for protected evaluation areas
