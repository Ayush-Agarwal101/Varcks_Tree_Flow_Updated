# llm/local_llama_client.py

import os
from dotenv import load_dotenv
load_dotenv()
import time
import random
import ollama
from openai import OpenAI
from llm.rate_limiter import TokenBucket
from langsmith import traceable

_nvidia_limiter = TokenBucket(rate=12, capacity=2)

# Global Config
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

# Unified call_llm. Switch provider using LLM_PROVIDER env variable.
@traceable(name="LLM Call")
def call_llm(prompt: str, model: str = "qwen2.5:7b", provider: str = None) -> str:
    """
    Returns plain string output. No streaming.
    """
    provider = provider or LLM_PROVIDER

    if provider == "ollama":
        return _call_ollama(prompt, model)

    elif provider == "nvidia":
        return _call_nvidia(prompt, model)

    else:
        raise ValueError(f"Unknown provider: {provider}")

# Ollama (Non-streaming)

def _call_ollama(prompt: str, model: str) -> str:
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"]


# NVIDIA (Non-streaming)

_client = None  # global reuse

def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY missing in .env")

        _client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
    return _client

def _call_nvidia(prompt: str, model: str) -> str:
    client = _get_client()

    for attempt in range(5):
        _nvidia_limiter.wait()

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                top_p=0.7,
                max_tokens=2048,
                stream=False
            )

            result = completion.choices[0].message.content
            time.sleep(0.2)
            return result

        except Exception as e:
            print(f"[NVIDIA ERROR] Attempt {attempt}: {str(e)}")
            if "429" in str(e) or "Too Many Requests" in str(e):
                sleep_time = (2 ** attempt) + random.uniform(0.5, 1.5)
                print(f"⚠️ 429 hit. Backing off for {sleep_time:.2f}s")

                time.sleep(sleep_time)

                # GLOBAL COOLDOWN (prevents cascade)
                if attempt >= 2:
                    print("🛑 Triggering global cooldown...")
                    time.sleep(8)
            else:
                raise

    raise RuntimeError("NVIDIA call failed after retries")