# run_integration.py

import shutil
import os
from core.integration.engine import IntegrationEngine

def has_real_issues(report):
    return (
        report.get("missing_producers") or
        report.get("multiple_producers") or
        report.get("type_conflicts")
    )

def prepare_working_dir(raw_dir: str, working_dir: str):
    """
    Reset working directory from raw YAMLs
    """

    if not os.path.exists(raw_dir):
        raise ValueError(f"[ERROR] RAW_DIR does not exist: {raw_dir}")

    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)

    shutil.copytree(raw_dir, working_dir)

    print("[RESET] Working directory recreated from raw YAMLs")

if __name__ == "__main__":
    RAW_DIR = "specs/raw/function_specs"
    WORKING_DIR = "specs/working/function_specs"

    # ALWAYS reset at start of run
    RESET = True
    if RESET:
        prepare_working_dir(RAW_DIR, WORKING_DIR)

    MAX_ITER = 3

    for i in range(MAX_ITER):
        print(f"\n====== ITERATION {i+1} ======\n")

        engine = IntegrationEngine(WORKING_DIR)
        engine.run(iteration = i)

        report = engine.get_results()["report"]

        if not has_real_issues(report):
            print("[STOP] System stabilized.")
            break