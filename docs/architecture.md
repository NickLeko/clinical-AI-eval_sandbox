Clinical AI Evaluation Sandbox Architecture
Overview

The Clinical AI Evaluation Sandbox simulates how a healthcare organization might evaluate a Large Language Model (LLM) before integrating it into clinical decision-support workflows.

The system evaluates model responses across several safety-relevant dimensions:

faithfulness to provided clinical context

citation accuracy

uncertainty calibration

potential clinical safety risks

The framework is intentionally lightweight and designed to run as an automated evaluation pipeline.

System Architecture

The system follows a modular evaluation pipeline.

Dataset → Prompt Construction → LLM Generation → Evaluation Layer → Result Storage → Summary Report

Each stage is separated so components can evolve independently.

Module Breakdown
1. Dataset Layer

Location: dataset/clinical_questions.csv

The dataset contains structured clinical evaluation cases.

Each row includes the following fields:

Field	Description
case_id	unique identifier
question	clinical decision-support question
provided_context	guideline excerpt or clinical evidence
expected_behavior	answer / uncertain / refuse
required_citations	citations that must appear in response
forbidden_actions	unsafe actions used for safety checks
category	evaluation scenario type
risk_level	low / medium / high

The dataset acts as a golden evaluation set used to probe model behavior.

2. Prompt Construction Layer

Location: src/prompt_templates.py

Prompts enforce a structured response format.

The model must produce sections including:

Recommendation

Rationale with citations

Uncertainty & Escalation

Do-not-do actions

Structured responses make automated evaluation possible.

3. Generation Layer

Location: src/generate_answers.py

This component:

Loads the evaluation dataset

Builds prompts using the template

Sends prompts to the LLM

Stores model responses

Outputs are saved to:

results/raw_generations.jsonl

Caching prevents repeated API calls when prompts have not changed.

4. Evaluation Layer

Locations:

src/metrics.py

src/run_evaluation.py

The evaluation layer analyzes model responses.

Metrics include:

Metric	Purpose
format_compliance	checks required response structure
citation_validity	detects fabricated citations
required_citations	verifies expected references
uncertainty_alignment	checks calibration of uncertainty
faithfulness_proxy	estimates grounding in provided context

Safety flags detect:

unsafe recommendations

contraindicated actions

fabricated citations

refusal failures

Evaluation results are written to:

results/evaluation_output.csv

5. Reporting Layer

Location: src/summarize_results.py

This component generates a human-readable evaluation report.

Output:

results/summary.md

The report includes:

PASS / WARN / FAIL distribution

metric averages

failure mode counts

worst performing cases

Evaluation Philosophy

Healthcare AI systems require stronger evaluation standards than typical AI tools.

This sandbox prioritizes:

safe refusals

evidence-backed reasoning

uncertainty disclosure

avoidance of unsafe recommendations

Rather than measuring only accuracy, the system emphasizes risk detection and safety signals.

Deployment Model

The evaluation pipeline is designed to run via GitHub Actions.

The workflow:

installs dependencies

generates model outputs

runs evaluation metrics

produces reports

commits results to the repository

This approach enables reproducible evaluation without requiring local infrastructure.

Limitations

This sandbox uses heuristic evaluation metrics and does not provide full clinical validation.

Limitations include:

faithfulness is approximated using lexical overlap

safety detection relies on rule-based patterns

model correctness is not adjudicated by clinicians

The system should therefore be viewed as an evaluation prototype, not a regulatory validation system.

Future Improvements

Potential extensions include:

multi-model benchmarking

LLM-as-judge scoring

clinician adjudication workflows

retrieval-based evaluation

dashboard visualization of results

Summary

The Clinical AI Evaluation Sandbox demonstrates how an AI system could be evaluated before deployment into healthcare workflows.

The project illustrates:

evaluation dataset design

structured prompting

automated safety scoring

reproducible evaluation pipelines
