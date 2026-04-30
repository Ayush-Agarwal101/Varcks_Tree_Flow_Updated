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

            elif action.action == "connect_variable":
                self._handle_connect_variable(action)

            elif action.action == "create_function":
                self._handle_create_function(action)

            elif action.action == "remove_producer":
                self._handle_remove_producer(action)

            elif action.action == "keep_only_producer":
                self._handle_keep_only_producer(action)

            elif action.action == "remove_variable":
                self._handle_remove_variable(action)

    # ---------------------------
    # ACTION HANDLERS
    # ---------------------------

    def _handle_remove_variable(self, action):
        var = action.target

        if not var:
            return

        for root, _, files in os.walk(self.yaml_dir):
            for file in files:
                if not file.endswith(".yaml"):
                    continue

                path = os.path.join(root, file)
                data = self._load_yaml(path)

                modified = False

                for fn in data.get("functions", []):
                    produces = fn.get("produces", [])

                    if var in produces:
                        produces.remove(var)
                        modified = True

                if modified:
                    self._save_yaml(path, data)

    def _handle_connect_variable(self, action):
        var = action.target
        fn_name = action.details.get("to_function")

        if not var or not fn_name:
            return

        for root, _, files in os.walk(self.yaml_dir):
            for file in files:
                if not file.endswith(".yaml"):
                    continue

                path = os.path.join(root, file)
                data = self._load_yaml(path)

                modified = False

                for fn in data.get("functions", []):
                    if fn["name"] == fn_name:

                        params = fn.setdefault("parameters", [])

                        if "." not in var:
                            return

                        entity, name = var.split(".", 1)

                        if not any(p["name"] == name for p in params):
                            params.append({
                                "name": name,
                                "type": "unknown",
                                "entity": entity
                            })
                            modified = True

                if modified:
                    self._save_yaml(path, data)

    def _handle_create_function(self, action):
        """
        Minimal safe function creation
        """
        if not action.target or "." not in action.target:
            return
        entity = action.target.split(".")[0]

        new_fn = {
            "name": f"process_{entity}",
            "parameters": [],
            "return_type": "unknown",
            "entity": entity,
            "produces": [action.target],
            "description": action.details.get("description", "")
        }

        # put in first YAML file (safe fallback)
        for root, _, files in os.walk(self.yaml_dir):
            for file in files:
                if file.endswith(".yaml"):
                    path = os.path.join(root, file)
                    data = self._load_yaml(path)

                    functions = data.setdefault("functions", [])

                    if not any(f["name"] == new_fn["name"] for f in functions):
                        functions.append(new_fn)

                    self._save_yaml(path, data)
                    return

    def _handle_remove_producer(self, action):
        var = action.target
        fn = action.details.get("function")

        if not var or not fn or "." not in fn:
            return

        file_name, fn_name = fn.rsplit(".", 1)

        filepath = self._find_yaml_file(file_name)
        if not filepath:
            return

        data = self._load_yaml(filepath)

        modified = False

        for f in data.get("functions", []):
            if f["name"] == fn_name:
                produces = f.get("produces", [])

                if var in produces:
                    produces.remove(var)
                    modified = True

        if modified:
            self._save_yaml(filepath, data)

    def _handle_keep_only_producer(self, action):
        var = action.target
        keep_fn = action.details.get("function")

        if not var or not keep_fn:
            return

        for root, _, files in os.walk(self.yaml_dir):
            for file in files:
                if not file.endswith(".yaml"):
                    continue

                path = os.path.join(root, file)
                data = self._load_yaml(path)
                file_name = data.get("file", "").replace(".yaml", "").replace(".yml", "")

                modified = False

                for f in data.get("functions", []):
                    fn_name = f.get("name")
                    produces = f.get("produces", [])

                    full_fn_name = f"{file_name}.{fn_name}"

                    if var in produces:
                        if full_fn_name != keep_fn:
                            produces.remove(var)
                            modified = True

                if modified:
                    self._save_yaml(path, data)
                
    def _handle_add_producer(self, action):
        """
        Add produces entry to a function
        """
        target = action.target  # e.g. user.user_id
        function = action.details.get("function")

        if not function or "." not in function:
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

    def _find_yaml_file(self, target_file_name):
        target_file_name = target_file_name.replace("\\", "/")

        for root, _, files in os.walk(self.yaml_dir):
            for file in files:
                if not file.endswith(".yaml"):
                    continue

                path = os.path.join(root, file)
                data = self._load_yaml(path)

                file_name = data.get("file", "").replace(".yaml", "").replace(".yml", "")

                if file_name == target_file_name:
                    return path

        return None

    def _load_yaml(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _save_yaml(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False)