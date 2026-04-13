# core/integration/engine.py

from typing import Dict

from .loader import YAMLLoader
from .detectors import IntegrationDetectors
from .linker import IntegrationLinker
from .reporter import IntegrationReporter


class IntegrationEngine:
    """
    Orchestrates full integration analysis pipeline.
    """

    def __init__(self, yaml_directory: str):
        self.yaml_directory = yaml_directory

        self.variables = {}
        self.report = {}
        self.links = []
        self.graph = {}

    # ---------------------------
    # STEP 1 — Load YAMLs
    # ---------------------------

    def load(self):
        loader = YAMLLoader()
        self.variables = loader.load_directory(self.yaml_directory)

    # ---------------------------
    # STEP 2 — Detect Issues
    # ---------------------------

    def detect(self):
        detectors = IntegrationDetectors(self.variables)
        self.report = detectors.run_all_checks()

    # ---------------------------
    # STEP 3 — Build Links + Graph
    # ---------------------------

    def build_links(self):
        linker = IntegrationLinker(self.variables)

        self.links = linker.build_variable_links()
        self.graph = linker.build_function_graph()

    # ---------------------------
    # STEP 4 — Report
    # ---------------------------

    def report_results(self):
        reporter = IntegrationReporter(
            report=self.report,
            links=self.links,
            graph=self.graph
        )

        reporter.print_errors()
        reporter.print_links()
        reporter.print_function_graph()
        reporter.print_summary()

    # ---------------------------
    # FULL PIPELINE
    # ---------------------------

    def run(self):
        print("\n=== INTEGRATION ENGINE START ===\n")

        self.load()
        print("YAMLs loaded.")

        self.detect()
        print("Detection complete.")

        self.build_links()
        print("Linking complete.")

        self.report_results()

        print("\n=== INTEGRATION ENGINE END ===\n")

    # ---------------------------
    # OPTIONAL: Get raw data
    # ---------------------------

    def get_results(self) -> Dict:
        return {
            "variables": self.variables,
            "report": self.report,
            "links": self.links,
            "graph": self.graph
        }