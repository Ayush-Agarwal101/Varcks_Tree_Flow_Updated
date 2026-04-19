# core/node_description_builder.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from dotenv import load_dotenv
from llm.local_llama_client import call_llm
load_dotenv()
from llm.batch_runner import run_batch


# Helper: Extract all nodes (folders + files)

def extract_all_nodes(tree, parents=None):
    if parents is None:
        parents = []

    results = []

    current_node = {
        "name": tree.get("name"),
        "type": tree.get("type"),
        "full_path": tree.get("full_path"),
        "description": tree.get("description", ""),
        "mandatory": tree.get("mandatory", "no"),
        "parents": parents.copy()
    }

    results.append(current_node)

    new_parents = parents + [{
        "name": tree.get("name"),
        "type": tree.get("type"),
        "full_path": tree.get("full_path")
    }]

    for child in tree.get("children", []):
        results.extend(extract_all_nodes(child, new_parents))

    return results

def call_with_retry(prompt, retries=2):
    for i in range(retries + 1):
        try:
            response = call_llm(prompt, provider="nvidia", model="meta/llama-3.3-70b-instruct")

            if not response or len(response.strip()) < 50:
                raise ValueError("Empty or too short response")
            return response

        except Exception as e:
            if i == retries:
                raise e

# Main Builder

def build_node_descriptions(
    pruned_structure_path: str,
    stack_meta_path: str,
    global_description_path: str,
    output_base_dir: str = "specs/node_descriptions"
):

    # Load inputs
    with open(pruned_structure_path, "r", encoding="utf-8") as f:
        pruned_structure = json.load(f)

    with open(stack_meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    with open(global_description_path, "r", encoding="utf-8") as f:
        global_description = f.read()

    user_requirement = meta["user_initial_prompt"]
    tech_stack_summary = meta["tech_stack_summary"]

    # Extract nodes
    all_nodes = extract_all_nodes(pruned_structure)

    os.makedirs(output_base_dir, exist_ok=True)

    system_prompt = """You are a senior software architect.

    Write concise, structured documentation for a project node.

    Rules:
    - Follow the exact section format.
    - Stay consistent with the given architecture and tech stack.
    - Do NOT introduce new layers or technologies.
    - Do NOT write code.
    - Keep descriptions short and precise.

    Function Rules:
    - Define clear function names.
    - Include parameter names only (no types).
    - Include return value (conceptual).
    - Keep descriptions 1–2 lines.
    """

    def process_node(node, user_requirement, tech_stack_summary, global_description, output_base_dir):

        parent_text = ""
        for p in node["parents"]:
            parent_text += f"- {p['name']} ({p['type']})\n"

        user_prompt = f"""USER REQUIREMENT:
        {user_requirement}

        TECH STACK:
        {tech_stack_summary}

        GLOBAL ARCHITECTURE:
        {global_description}

        CURRENT NODE:
        Name: {node['name']}
        Type: {node['type']}
        Full Path: {node['full_path']}
        Description: {node['description']}
        Mandatory: {node['mandatory']}

        PARENT HIERARCHY:
        {parent_text}

        Output Format (STRICT):

        # {node['full_path']}

        ## Purpose
        (1–2 lines)

        ## Responsibilities
        - bullet points

        ## Key Functions (Conceptual)
        - function_name(param1, param2) -> return_value
          - description

        ## Interactions
        - bullet points

        ## Future Extensibility
        - bullet points

        Constraints:
        - Every file MUST include "Key Functions (Conceptual)"
        - Keep output concise
        - No code
        - No JSON
        """

        full_prompt = system_prompt + "\n\n" + user_prompt

        print(f"Generating description for: {node['full_path']}")

        try:
            response = call_with_retry(full_prompt)
        except Exception as e:
            print(f"[ERROR] Failed for {node['full_path']}: {e}")
            return

        safe_path = node["full_path"].replace("\\", "/").strip("/")
        output_path = os.path.join(output_base_dir, safe_path + ".md")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response)

    tasks = []

    for node in all_nodes:
        def make_task(node=node):
            def task():
                process_node(
                    node,
                    user_requirement,
                    tech_stack_summary,
                    global_description,
                    output_base_dir
                )

            return task

        tasks.append(make_task())

    run_batch(tasks, max_workers=2)

    print("\nAll node descriptions generated successfully.")

# CLI

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pruned", required=True)
    parser.add_argument("--meta", required=True)
    parser.add_argument("--global-desc", required=True)
    parser.add_argument("--output-dir", default="specs/node_descriptions")
    args = parser.parse_args()

    build_node_descriptions(
        pruned_structure_path=args.pruned,
        stack_meta_path=args.meta,
        global_description_path=args.global_desc,
        output_base_dir=args.output_dir
    )