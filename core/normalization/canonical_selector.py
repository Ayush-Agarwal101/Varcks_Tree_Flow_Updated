# core/normalization/canonical_selector.py

from typing import List, Dict
from core.llm_structured import StructuredLLM
from pydantic import BaseModel

# Schema

class CanonicalFunction(BaseModel):
    name: str
    parameters: List[str]
    produces: List[str]

class CanonicalDecision(BaseModel):
    canonical: CanonicalFunction
    mappings: Dict[str, str]   # old_var → new_var

# Selector

class CanonicalSelector:

    def __init__(self, model=None):
        self.llm = StructuredLLM(provider="nvidia", model="meta/llama-3.3-70b-instruct")

    def build_prompt(self, cluster):

        text = "Functions:\n\n"

        for i, fn in enumerate(cluster):
            text += f"""
Function {i+1}:
Name: {fn.name}
Parameters: {fn.parameters}
Produces: {fn.produces}
Description: {fn.description}
"""

        text += """

Task:
- These functions represent similar behavior.
- Choose ONE canonical function that best represents all.
- Normalize parameter names and output variables.
- Provide mappings for all variants to canonical.

Return JSON:

{
  "canonical": {
    "name": "...",
    "parameters": ["..."],
    "produces": ["entity.variable"]
  },
  "mappings": {
    "old": "new"
  }
}
"""
        return text

    def select(self, cluster):
        prompt = self.build_prompt(cluster)

        result: CanonicalDecision = self.llm.call(
            prompt=prompt,
            schema=CanonicalDecision
        )

        return result