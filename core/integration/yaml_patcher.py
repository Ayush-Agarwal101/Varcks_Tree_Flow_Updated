# core/integration/yaml_patcher.py

import os
import yaml
from typing import Dict

class YAMLPatcher:

    def __init__(self, yaml_dir: str):
        self.yaml_dir = yaml_dir

    # ---------------------------
    # APPLY PLAN
    # ---------------------------

    def apply_plan(self, plan):
        for action in plan.actions:

            if action.action == "add_producer":
                self._handle_add_producer(action)

            elif action.action == "map_variable":
                self._handle_map_variable(action)

            elif action.action == "change_type":
                self._handle_change_type(action)

    # ---------------------------
    # ACTION HANDLERS
    # ---------------------------

    def _handle_add_producer(self, action):
        """
        Add produces entry to a function
        """
        target = action.target  # e.g. user.user_id
        function = action.details.get("function")

        if not function:
            return

        file_name, fn_name = function.rsplit(".", 1)

        filepath = self._find_yaml_file(file_name)
        if not filepath:
            return

        data = self._load_yaml(filepath)

        for fn in data.get("functions", []):
            if fn["name"] == fn_name:

                produces = fn.setdefault("produces", [])

                if target not in produces:
                    produces.append(target)

        self._save_yaml(filepath, data)

    def _handle_map_variable(self, action):
        """
        Add source mapping to parameters
        """
        source = action.details.get("from")
        target = action.details.get("to")

        if not source or not target:
            return

        # simple version: just print for now
        print(f"[MAP] {source} → {target}")

    def _handle_change_type(self, action):
        """
        Fix type inconsistencies
        """
        target = action.target
        new_type = action.details.get("type")

        if not new_type:
            return

        # simple version: just print for now
        print(f"[TYPE FIX] {target} → {new_type}")

    # ---------------------------
    # FILE HELPERS
    # ---------------------------

    def _find_yaml_file(self, file_name):
        for root, _, files in os.walk(self.yaml_dir):
            for file in files:
                if file.endswith(".yaml"):
                    path = os.path.join(root, file)
                    if file_name in path:
                        return path
        return None

    def _load_yaml(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _save_yaml(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False)