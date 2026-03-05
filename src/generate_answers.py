import argparse
import hashlib
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd
from tqdm import tqdm

from src.llm_clients import OpenAIClient, MockClient
from src.prompt_templates import build_clinical_prompt


RESULTS_DIR = "results"
RAW_OUT_PATH = os.path.join(RESULTS_DIR, "raw_generations.jsonl")


def ensure_results_dir() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)


def stable_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def load_existing_cache(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Loads existing generations so we don't re-call the LLM for unchanged cases.
    Returns dict keyed by cache_key.
    """
    if not os.path.exists(path):
        return {}

    cache: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            cache_key = row.get("cache_key")
            if cache_key:
                cache[cache_key] = row
    return cache


def write_jsonl_append(path: str, obj: Dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def build_cache_key(case_id: str, model_id: str, prompt_version: str, prompt: str) -> str:
    return stable_hash(f"{case_id}|{model_id}|{prompt_version}|{prompt}")


def select_client(provider: str, model_id: str):
    if provider == "openai":
        return OpenAIClient(model=model_id)
    if provider == "mock":
        return MockClient()
    raise ValueError(f"Unknown provider: {provider}")


def main(
    dataset_path: str,
    provider: str,
    model_id: str,
    prompt_version: str,
    max_cases: Optional[int],
    sleep_s: float,
) -> None:
    ensure_results_dir()

    df = pd.read_csv(dataset_path)
    if "case_id" not in df.columns:
        raise ValueError("Dataset must include a 'case_id' column")

    # Optional cap (cost control)
    if max_cases is not None:
        df = df.head(max_cases)

    client = select_client(provider, model_id)

    existing = load_existing_cache(RAW_OUT_PATH)

    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Generating"):
        case_id = str(row["case_id"])
        question = str(row.get("question", ""))
        context = str(row.get("provided_context", ""))

        prompt = build_clinical_prompt(question=question, context=context)
        cache_key = build_cache_key(case_id, model_id, prompt_version, prompt)

        # Skip if already generated for this exact prompt+model
        if cache_key in existing:
            continue

        t0 = time.time()
        resp = client.generate(prompt)
        latency_ms = int((time.time() - t0) * 1000)

        out = {
            "run_id": run_id,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "case_id": case_id,
            "provider": provider,
            "model_id": model_id,
            "prompt_version": prompt_version,
            "cache_key": cache_key,
            "prompt": prompt,
            "answer_text": resp.get("answer_text", ""),
            "latency_ms": latency_ms,
            # keep raw response for debugging; may be large but useful
            "raw_response": resp.get("raw_response", {}),
        }

        write_jsonl_append(RAW_OUT_PATH, out)

        if sleep_s > 0:
            time.sleep(sleep_s)

    print(f"Done. Raw generations at: {RAW_OUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate LLM answers for clinical eval dataset.")
    parser.add_argument("--dataset", default="dataset/clinical_questions.csv", help="Path to dataset CSV.")
    parser.add_argument("--provider", default="openai", choices=["openai", "mock"], help="LLM provider.")
    parser.add_argument("--model", default="gpt-4.1-mini", help="Model id (provider-specific).")
    parser.add_argument("--prompt-version", default="v1", help="Prompt template version string.")
    parser.add_argument("--max-cases", type=int, default=None, help="Max number of cases to run (cost control).")
    parser.add_argument("--sleep-s", type=float, default=0.0, help="Sleep between calls (rate-limit friendliness).")
    args = parser.parse_args()

    main(
        dataset_path=args.dataset,
        provider=args.provider,
        model_id=args.model,
        prompt_version=args.prompt_version,
        max_cases=args.max_cases,
        sleep_s=args.sleep_s,
    )
