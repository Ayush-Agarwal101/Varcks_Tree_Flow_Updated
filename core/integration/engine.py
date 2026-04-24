from typing import Dict

from .loader import YAMLLoader
from .detectors import IntegrationDetectors
from .linker import IntegrationLinker
from .reporter import IntegrationReporter
from core.normalization.build_canonical_map import build_canonical_maps
from core.integration.canonical_rewriter import CanonicalRewriter
from core.integration.canonical_injector import CanonicalInjector

class IntegrationEngine:
    """
    Full integration pipeline:
    - canonical mapping
    - injection
    - rewriting
    - adaptation
    - validation
    - linking
    """

    def __init__(self, yaml_directory: str):
        self.yaml_directory = yaml_directory

        self.variables = {}
        self.report = {}
        self.links = []
        self.graph = {}

    # STEP 0 — Canonical Mapping + Injection + Rewrite

    def apply_canonical_pipeline(self):
        print("Building canonical maps...")

        maps = build_canonical_maps(self.yaml_directory)

        function_map = maps["function_map"]
        variable_map = maps["variable_map"]
        canonical_functions = maps["canonical_functions"]

        print("Injecting canonical functions...")
        injector = CanonicalInjector(
            yaml_dir=self.yaml_directory,
            canonical_functions=canonical_functions
        )
        injector.inject()

        print("Rewriting YAMLs...")
        rewriter = CanonicalRewriter(
            yaml_dir=self.yaml_directory,
            function_map=function_map,
            variable_map=variable_map
        )
        rewriter.rewrite_all()

        print("Canonical pipeline complete.")

    # STEP 1 — Load YAMLs

    def load(self):
        loader = YAMLLoader()
        self.variables = loader.load_directory(self.yaml_directory)

    # STEP 2 —  Detect Issues

    def detect(self):
        detectors = IntegrationDetectors(self.variables)
        self.report = detectors.run_all_checks()

    # STEP 3 — Build Links + Graph

    def build_links(self):
        linker = IntegrationLinker(self.variables)

        self.links = linker.build_variable_links()
        self.graph = linker.build_function_graph()

    # STEP 4 — Report

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

    # FULL PIPELINE

    def run(self):
        print("\n=== INTEGRATION ENGINE START ===\n")

        self.apply_canonical_pipeline()

        self.load()
        print(type(next(iter(self.variables.values()))))
        print(vars(next(iter(self.variables.values()))))
        print("YAMLs loaded.")

        self.detect()
        print("Detection complete.")

        self.build_links()
        print("Linking complete.")

        self.report_results()

        print("\n=== INTEGRATION ENGINE END ===\n")

    # OPTIONAL: Get raw data

    def get_results(self) -> Dict:
        return {
            "variables": self.variables,
            "report": self.report,
            "links": self.links,
            "graph": self.graph
        }