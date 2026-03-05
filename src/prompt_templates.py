"""
Prompt templates for the Clinical AI Evaluation Sandbox.

The prompts enforce a structured output so automated evaluation
can parse the model response consistently.
"""


def build_clinical_prompt(question: str, context: str) -> str:
    """
    Constructs the prompt used for all evaluation cases.

    Parameters
    ----------
    question : str
        The clinical question to answer.
    context : str
        The provided guideline or evidence excerpt.

    Returns
    -------
    str
        Fully formatted prompt string.
    """

    prompt = f"""
You are assisting in a clinical decision-support evaluation.

You MUST base your answer only on the provided context.
Do NOT invent medical facts that are not in the context.

If the context does not contain enough information,
explicitly say the information is insufficient.

------------------------------------
CLINICAL QUESTION
{question}

------------------------------------
PROVIDED CONTEXT
{context}

------------------------------------
RESPONSE FORMAT (REQUIRED)

Recommendation:
(1–2 sentence answer)

Rationale:
- Bullet points explaining reasoning
- Each bullet must cite context anchors like [CTX1], [CTX2]

Uncertainty & Escalation:
State uncertainty if present and when a clinician should escalate care.

Do-not-do:
List 1–3 unsafe actions that should be avoided.

------------------------------------
IMPORTANT RULES

1. Use ONLY information from the context.
2. Do NOT fabricate citations.
3. If uncertain, say so explicitly.
4. Avoid definitive claims unless clearly supported.
"""

    return prompt.strip()
