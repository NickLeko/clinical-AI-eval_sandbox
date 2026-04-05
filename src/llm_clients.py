import os
import time
from typing import Any, Dict

import requests


class LLMGenerationError(RuntimeError):
    pass


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

    def __init__(
        self,
        model: str = "gpt-4o",
        timeout_s: float = 60.0,
        max_retries: int = 3,
        retry_backoff_s: float = 1.0,
    ):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.retry_backoff_s = retry_backoff_s

    def _extract_answer_text(self, data: Dict[str, Any]) -> str:
        try:
            answer_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMGenerationError(
                f"OpenAI response was missing the assistant message content for model '{self.model}'."
            ) from exc

        if not isinstance(answer_text, str) or not answer_text.strip():
            raise LLMGenerationError(f"OpenAI returned an empty assistant message for model '{self.model}'.")

        return answer_text

    def _http_error_message(self, response: requests.Response) -> str:
        try:
            details = response.json()
        except ValueError:
            details = response.text[:500]
        return f"OpenAI API request failed with status {response.status_code}: {details}"

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
            "temperature": 0.2,
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_s,
                )
                if not response.ok:
                    raise LLMGenerationError(self._http_error_message(response))

                data = response.json()
                answer_text = self._extract_answer_text(data)

                return {
                    "answer_text": answer_text,
                    "raw_response": data,
                }
            except (requests.RequestException, LLMGenerationError, ValueError) as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break
                time.sleep(self.retry_backoff_s * (2 ** (attempt - 1)))

        raise LLMGenerationError(
            f"OpenAI generation failed after {self.max_retries} attempts for model '{self.model}': {last_error}"
        )


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
            "raw_response": {"mock": True},
        }
