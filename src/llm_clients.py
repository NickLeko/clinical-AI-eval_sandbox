import os
import requests
from typing import Dict, Any


class BaseLLMClient:
    """
    Abstract interface for LLM clients.
    Allows swapping providers without touching evaluation code.
    """

    def generate(self, prompt: str) -> Dict[str, Any]:
        raise NotImplementedError


class OpenAIClient(BaseLLMClient):
    """
    Minimal OpenAI REST client.

    Uses the chat completions endpoint.
    Designed intentionally lightweight so the repo has minimal dependencies.
    """

    def __init__(self, model: str = "gpt-4o"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    def generate(self, prompt: str) -> Dict[str, Any]:

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a careful clinical decision-support assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2
        }

        response = requests.post(self.endpoint, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()

        answer_text = data["choices"][0]["message"]["content"]

        return {
            "answer_text": answer_text,
            "raw_response": data
        }


class MockClient(BaseLLMClient):
    """
    Used when running tests without API access.
    Produces deterministic dummy outputs.
    """

    def generate(self, prompt: str) -> Dict[str, Any]:

        dummy_answer = """
Recommendation:
Insufficient information to provide a definitive recommendation.

Rationale:
- The provided context is limited. [CTX1]

Uncertainty & Escalation:
Further clinical evaluation is recommended.

Do-not-do:
- Do not initiate treatment without clinician review.
"""

        return {
            "answer_text": dummy_answer.strip(),
            "raw_response": {"mock": True}
        }
