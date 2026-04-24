# run_integration.py

import shutil
import os
from core.integration.engine import IntegrationEngine

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

    # Step 0: Reset working dir
    prepare_working_dir(RAW_DIR, WORKING_DIR)

    # Step 1: Run integration on working copy
    engine = IntegrationEngine(WORKING_DIR)
    engine.run()