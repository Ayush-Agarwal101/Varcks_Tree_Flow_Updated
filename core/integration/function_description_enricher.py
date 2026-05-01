# core/integration/function_description_enricher.py

from core.llm_structured import StructuredLLM
from core.integration.function_schema import BatchFunctionDescriptions
import json
import os

class FunctionDescriptionEnricher:
    def __init__(self):
        self.llm = StructuredLLM()
        self.cache_path = "outputs/function_descriptions_cache.json"
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        with open(self.cache_path, "w") as f:
            json.dump(self.cache, f, indent=2)

    def enrich(self, functions: dict) -> dict:
        if not functions:
            return functions

        missing = {}

        for fn, data in functions.items():
            if fn in self.cache:
                functions[fn]["description"] = self.cache[fn]
            else:
                missing[fn] = data

            if not missing:
                return functions

        fn_items = list(missing.items())

        prompt_lines = []

        for fn_name, data in fn_items:
            prompt_lines.append(
                f"{fn_name} | inputs: {data.get('inputs')} | outputs: {data.get('outputs')}"
            )

        prompt = f"""
You are analyzing backend/frontend functions.

For EACH function, write a short, precise description of what it does.

Functions:
{chr(10).join(prompt_lines)}

Rules:
- Be concise (1 line)
- Focus on purpose, not implementation
- Do NOT hallucinate
- Use names + inputs/outputs

Return JSON:

{{
  "function_full_path": {{
    "description": "..."
  }}
}}
"""

        try:
            result: BatchFunctionDescriptions = self.llm.call(
                prompt=prompt,
                schema=BatchFunctionDescriptions
            )

            for fn, desc_obj in result.root.items():
                if fn in functions:
                    functions[fn]["description"] = desc_obj.description
                    self.cache[fn] = desc_obj.description

        except Exception as e:
            print("[DESCRIPTION ENRICHER ERROR]", str(e))

        if missing:
            self._save_cache()

        return functions