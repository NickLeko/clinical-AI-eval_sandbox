# Clinical AI Evaluation Sandbox Safety Case

## Purpose

This document outlines the safety reasoning behind the Clinical AI Evaluation Sandbox.

The goal is to demonstrate how a healthcare organization might evaluate and risk-assess a Large Language Model (LLM) before integrating it into clinical decision-support workflows.

This project is not a clinical device.  
It is an **evaluation prototype designed to surface potential safety risks.**

---

## Intended Use

The sandbox evaluates LLM responses to clinical decision-support questions using structured prompts and automated scoring.

The system is intended to:

- test how models respond to clinical scenarios
- detect unsafe or hallucinated recommendations
- evaluate citation grounding
- evaluate uncertainty calibration

The system does **not provide medical advice** and is not used for patient care.

---

## System Boundary

The evaluation system includes:

- clinical evaluation dataset
- prompt construction layer
- model generation layer
- automated evaluation metrics
- reporting pipeline

The system does not include:

- electronic health record integration
- patient-specific decision making
- clinician user interface
- production deployment infrastructure

---

## Hazard Identification

Potential hazards when deploying LLMs in healthcare include:

### H1 — Hallucinated Clinical Facts

The model invents medical facts not supported by evidence.

Example:

- inventing a contraindication
- inventing a medication interaction
- inventing guideline recommendations

---

### H2 — Unsafe Treatment Recommendations

The model recommends actions that may harm a patient.

Examples:

- prescribing contraindicated medications
- suggesting unsafe dosing
- ignoring critical symptoms

---

### H3 — Overconfident Responses

The model expresses certainty despite incomplete information.

Example:

- diagnosing without adequate context
- failing to acknowledge uncertainty

---

### H4 — Failure to Refuse

The model provides an answer when the correct behavior should be refusal.

Example:

- answering questions without sufficient evidence
- giving treatment advice outside provided context

---

## Risk Mitigations

The sandbox implements several mitigations to detect these hazards.

### Structured Prompting

Prompts enforce structured responses including:

- recommendation
- rationale with citations
- uncertainty and escalation
- do-not-do actions

This structure improves interpretability and evaluation reliability.

---

### Citation Requirements

Models are required to reference context anchors such as:

CTX1  
CTX2  
CTX3

Evaluation detects fabricated citations.

---

### Forbidden Action Detection

Dataset cases may include forbidden actions.

Examples:

- prescribing NSAIDs in CKD stage 4
- ignoring severe allergic reactions

Evaluation flags responses containing unsafe actions.

---

### Uncertainty Evaluation

The system evaluates whether the model appropriately:

- acknowledges uncertainty
- refuses when context is insufficient
- avoids confident language

---

### Automated Safety Flags

The evaluation layer applies safety flags including:

- unsafe recommendation
- unsupported citation
- refusal failure
- hallucination suspicion

Safety flags cause a case to fail evaluation.

---

## Human-in-the-Loop Review

In real clinical AI systems, automated evaluation must be supplemented with human review.

Typical workflow:

1. automated evaluation identifies flagged cases
2. clinicians review flagged responses
3. failure patterns are categorized
4. prompts or guardrails are updated

The sandbox simulates this by generating **flagged case reports.**

---

## Monitoring Concept (Production Systems)

If deployed in a production environment, additional monitoring would be required:

- model drift monitoring
- prompt regression testing
- unsafe output detection
- clinician feedback loops

These mechanisms are outside the scope of this sandbox but are documented for completeness.

---

## Residual Risk

Even with mitigations, LLM systems carry residual risks.

Remaining risks include:

- subtle hallucinations that pass heuristic checks
- context misinterpretation
- incomplete medical knowledge

Therefore, LLM systems should operate under **clinician supervision**.

---

## Limitations of This Safety Case

This document represents a simplified safety analysis.

Limitations include:

- no formal risk matrix
- no clinician validation
- heuristic evaluation metrics
- limited dataset size

The document is intended to demonstrate **risk-aware system thinking**, not regulatory compliance.

---

## Summary

The Clinical AI Evaluation Sandbox demonstrates how healthcare AI systems can be evaluated with safety in mind.

Key principles include:

- structured prompting
- automated safety detection
- explicit uncertainty handling
- human review of flagged outputs

These practices help reduce the risk of unsafe AI behavior before deployment.
