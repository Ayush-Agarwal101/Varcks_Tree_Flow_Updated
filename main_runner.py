# main_runner.py
# Run:
# python main_runner.py --json-file data/Web_Dev_Only.json --start-node "Core Application & Web Stacks" --initial-prompt "build a backend for online bakery shop that sells cakes"

import os
import json
import argparse
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from core.langgraph_runner import LangGraphRecorder
from core.llm_structured import StructuredLLM
from core.schemas import NodeDecision
from dotenv import load_dotenv

load_dotenv()
from langsmith import traceable

# LLM CLIENT

class LLMClient:
    def __init__(self, model: str = None):
        self.structured = StructuredLLM(model=model)

    @traceable(name="Choose Option")
    def choose_option(self, prompt: str, options: List[str]) -> NodeDecision:
        if not options:
            raise ValueError("No options available for selection.")

        options_text = " | ".join(f"{i + 1} {opt}" for i, opt in enumerate(options))

        formatted_prompt = f"""
        You are navigating a predefined decision tree.

        Your task is NOT to generate a project structure.
        Your task is ONLY to select ONE option from the provided list.

        USER REQUIREMENT:
        {prompt}

        AVAILABLE OPTIONS (choose exactly one):
        {options_text}

        Rules:
        - Choose choice ONLY by index (number)
        - Do NOT return option text or a list
        - Do NOT output anything except JSON

        Return ONLY valid JSON in this exact format:

        {{
          "choice": 1,
          "rationale": "short",
          "purpose": "short"
        }}
        """

        # response is a NodeDecision object returned by this function
        response: NodeDecision = self.structured.call(
            prompt=formatted_prompt,
            schema=NodeDecision
        )

        # --------- HARD DETERMINISTIC VALIDATION ---------
        choice_index = response.choice

        # Try converting to int (handles cases like "2", [2], etc.)
        try:
            if isinstance(choice_index, list):
                choice_index = choice_index[0]
            choice_index = int(choice_index)
        except Exception:
            # fallback (never break traversal)
            choice_index = 1

        # Clamp to valid range
        choice_index = max(1, min(choice_index, len(options)))

        # --------- STORE BOTH INDEX + VALUE ---------
        response.choice_index = choice_index
        response.choice_name = options[choice_index - 1]

        return response


# TREE UTILITIES

def load_tree_from_file(filename: str) -> Any:
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def find_key_recursive(obj: Any, target_key: str) -> Optional[Tuple[str, Any]]:
    if isinstance(obj, dict):
        if target_key in obj:
            return target_key, obj[target_key]
        for k, v in obj.items():
            res = find_key_recursive(v, target_key)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_key_recursive(item, target_key)
            if res:
                return res
    return None


def extract_children_from_value(value: Any) -> List[Tuple[str, Any]]:
    children = []

    if isinstance(value, dict):
        for k, v in value.items():
            children.append((k, v))

    elif isinstance(value, list):
        for i, item in enumerate(value):
            if isinstance(item, dict) and len(item) == 1:
                key = list(item.keys())[0]
                children.append((key, item[key]))
            else:
                children.append((str(item), item))

    return children


# TRAVERSAL

@dataclass  # This class is mainly used to store data, so automatically create useful methods like init, repr, eq for it So you don’t need to write them manually.
class BranchState:
    path: List[str]  # technology stack selected so far
    node_name: str  # current node name in the decision tree
    node_value: Any  # The subtree under the current node
    prompt: str  # original user prompt


@traceable(name="Decision Traversal")
def traverse(tree: Any, start_node_name: str, llm: LLMClient, base_prompt: str):
    found = find_key_recursive(tree, start_node_name)
    if not found:
        raise ValueError(f"Start node '{start_node_name}' not found.")

    start_name, start_value = found  # tuple unpacking

    recorder = LangGraphRecorder()

    branch = BranchState(
        path=[],
        node_name=start_name,
        node_value=start_value,
        prompt=base_prompt.strip()
    )

    completed_path = []

    while True:
        recorder.add_node(branch.node_name)
        children = extract_children_from_value(branch.node_value)

        if not children:
            recorder.mark_leaf(branch.node_name)
            completed_path = branch.path
            break

        child_names = [c[0] for c in children]
        options_text = " | ".join(f"{i + 1} {name}" for i, name in enumerate(child_names))

        # Build contextual prompt for this decision

        selected_stack_text = (
            "None yet"
            if not branch.path
            else " → ".join(branch.path)
        )

        decision_prompt = f"""
        User Requirement:
        {base_prompt}

        Selected Stack So Far:
        {selected_stack_text}

        Current Decision Node:
        {branch.node_name}

        Available Options:
        {options_text}

        Choose the single best option for the project.
        """

        decision = llm.choose_option(decision_prompt, child_names)

        chosen_name = decision.choice_name

        recorder.add_choice_rationale(
            parent_node=branch.node_name,
            choice=chosen_name,
            rationale=decision.rationale,
            purpose=decision.purpose
        )

        recorder.add_prompt_to_node(branch.node_name, decision_prompt)
        recorder.add_choice(
            branch.node_name,
            [{
                "index": decision.choice_index,
                "name": decision.choice_name
            }]
        )

        def normalize(s):
            return s.strip().lower()

        matched = next(
            (c for c in children if normalize(c[0]) == normalize(chosen_name)),
            None
        )

        if not matched:
            print("\nDEBUG ERROR")
            print("OPTIONS:", child_names)
            print("CHOICE INDEX:", decision.choice_index)
            print("CHOICE NAME:", decision.choice_name)
            print("CHILDREN:", [c[0] for c in children])
            raise RuntimeError("Internal traversal mismatch.")

        child_name, child_value = matched

        recorder.add_edge(branch.node_name, child_name)

        recorder.add_prompt_to_edge(
            branch.node_name,
            child_name,
            decision_prompt
        )

        branch = BranchState(
            path=branch.path + [child_name],
            node_name=child_name,
            node_value=child_value,
            prompt=base_prompt
        )

    return completed_path, recorder


# FINAL PROMPT BUILDER

def build_clean_final_prompt(initial_prompt, tech_stack, recorder):
    prompt = f"""# Project Specification

## User Requirement
{initial_prompt.strip()}

## Selected Technology Stack

"""

    for i, tech in enumerate(tech_stack):
        prompt += f"### {i + 1}. {tech}\n"

        parent = tech_stack[i - 1] if i > 0 else None
        data = recorder.choice_rationales.get((parent, tech))

        if data:
            prompt += f"**Why chosen:** {data.get('rationale')}\n"
            prompt += f"**Purpose:** {data.get('purpose')}\n"

        prompt += "\n"

    prompt += "## Technology Stack Summary\n"
    prompt += " → ".join(tech_stack)

    return prompt


# CLI

if __name__ == "__main__":

    parser = argparse.ArgumentParser()      # creates an argument parser object
    parser.add_argument("--json-file", required=True)
    parser.add_argument("--start-node", required=True)
    parser.add_argument("--initial-prompt")
    parser.add_argument("--output-image", default="outputs/langgraph_output")
    parser.add_argument("--output-meta", default="data/stack_meta.json")
    args = parser.parse_args()          # reads the command line input
    if not args.initial_prompt or not args.initial_prompt.strip():
        args.initial_prompt = input("Enter initial prompt: ").strip()

    tree = load_tree_from_file(args.json_file)
    llm = LLMClient()

    tech_stack, recorder = traverse(
        tree,
        args.start_node,
        llm,
        args.initial_prompt
    )

    image_dir = os.path.dirname(args.output_image)      # extracts the directory part of a path
    if image_dir:           # checks whether the directory string is not empty (the path is just a filename with no folder)
        os.makedirs(image_dir, exist_ok=True)

    outpath = recorder.render(args.output_image)

    # Save final prompt
    os.makedirs("specs", exist_ok=True)

    final_prompt = build_clean_final_prompt(
        args.initial_prompt,
        tech_stack,
        recorder
    )

    with open("specs/final_prompt.txt", "w", encoding="utf-8") as f:
        f.write(final_prompt)

    # Convert tuple keys to string keys for JSON safety
    formatted_choices = {}

    for (parent, choice), data in recorder.choice_rationales.items():
        key = f"{parent} -> {choice}"
        formatted_choices[key] = data

    # Save meta JSON
    meta = {
        "user_initial_prompt": args.initial_prompt,
        "tech_stack": tech_stack,
        "tech_stack_summary": " → ".join(tech_stack),
        "technology_choices": formatted_choices,
        "nodes": {
            n: {
                "is_leaf": recorder.nodes[n].is_leaf,
                "choices": recorder.node_choices.get(n, [])     # Get the choices for node n. If the node does not exist, return an empty list [].
            }
            for n in recorder.nodes
        },
        "edges": recorder.edges
    }

    os.makedirs(os.path.dirname(args.output_meta), exist_ok=True)

    with open(args.output_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("\nFINAL PROMPT SAVED TO specs/final_prompt.txt")
    print(f"Graph saved to: {outpath}")
    print(f"Meta saved to: {args.output_meta}")