# run_integration.py

from core.integration.engine import IntegrationEngine

if __name__ == "__main__":

    YAML_DIR = "specs/function_specs"

    engine = IntegrationEngine(YAML_DIR)
    engine.run()