# llm/local_llama_client.py

import os
from dotenv import load_dotenv
load_dotenv()

import ollama
from openai import OpenAI
from llm.rate_limiter import RateLimiter
from langsmith import traceable

_nvidia_limiter = RateLimiter(40)

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

def _call_nvidia(prompt: str, model: str) -> str:
    _nvidia_limiter.wait()

    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key:
        raise ValueError("NVIDIA_API_KEY missing in .env")

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )
    try:
        completion = client.chat.completions.create(model=model,messages=[{"role": "user", "content": prompt}],temperature=0.0,top_p=0.7,max_tokens=4096, stream=False)

        return completion.choices[0].message.content

    except Exception as e:
        raise RuntimeError(f"NVIDIA call failed: {str(e)}")