# core/integration/engine.py

from typing import Dict
import os
import copy
from .loader import YAMLLoader
from .detectors import IntegrationDetectors
from .linker import IntegrationLinker
from .reporter import IntegrationReporter
from core.normalization.build_canonical_map import build_canonical_maps
from core.integration.canonical_rewriter import CanonicalRewriter
from core.integration.canonical_injector import CanonicalInjector
from core.integration.repair_engine import RepairEngine, RepairAction
from core.integration.yaml_patcher import YAMLPatcher
from core.integration.graph_visualizer import GraphVisualizer
from core.integration.repair_logger import RepairLogger
from core.integration.suggestion_parser import SuggestionParser
from core.integration.validator import ActionValidator
from core.integration.system_registry import SystemRegistryBuilder
from core.integration.flow_reasoner import FlowReasoner
from core.integration.unused_reasoner import UnusedOutputReasoner
from core.integration.function_description_enricher import FunctionDescriptionEnricher

def deduplicate(actions):
    seen = set()
    result = []

    for a in actions:
        try:
            key = (a.action, a.target, str(a.details))
        except AttributeError:
            continue

        if key in seen:
            continue

        seen.add(key)
        result.append(a)

    return result

class IntegrationEngine:
    def __init__(self, yaml_directory: str):
        self.yaml_directory = yaml_directory

        self.variables = {}
        self.report = {}
        self.links = []
        self.graph = {}
        self.prev_variables = {}
        self.enricher = FunctionDescriptionEnricher()

    def _print_variable_changes(self):
        if not self.prev_variables:
            print("[DEBUG] Initial load (no previous state)")
            return

        print("\n[DEBUG] Variable Changes:")

        changes = 0

        for key, var in self.variables.items():
            prev = self.prev_variables.get(key)

            if not prev:
                print(f"  [+] NEW VARIABLE: {key}")
                changes += 1
                continue

            if set(var.produced_by) != set(prev.produced_by):
                print(f"  [P] {key}")
                print(f"     OLD producers: {prev.produced_by}")
                print(f"     NEW producers: {var.produced_by}")
                changes += 1

            if set(var.used_by) != set(prev.used_by):
                print(f"  [U] {key}")
                print(f"     OLD used_by: {prev.used_by}")
                print(f"     NEW used_by: {var.used_by}")
                changes += 1

        if changes == 0:
            print("  No changes detected.")

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

    def load(self, iteration = 0):
        loader = YAMLLoader()

        prev_snapshot = copy.deepcopy(self.variables)
        self.variables = loader.load_directory(self.yaml_directory)
        if iteration == 0:
            for k, v in list(self.variables.items())[:10]:
                print(k, v.produced_by, v.used_by)
        else:
            self.prev_variables = prev_snapshot
            self._print_variable_changes()

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
        # reporter.print_links()
        # reporter.print_function_graph()
        reporter.print_summary()

    # FULL PIPELINE

    def run(self, iteration = 0):
        print("\n=== INTEGRATION ENGINE START ===\n")

        if iteration == 0:
            self.apply_canonical_pipeline()

        print("RUNNING ON:", self.yaml_directory)

        self.load(iteration)
        self.detect()
        self.build_links()

        # SAVE BEFORE STATE
        before_variables = copy.deepcopy(self.variables)
        before_report = copy.deepcopy(self.report)

        viz = GraphVisualizer(self.graph)

        os.makedirs("outputs/debug", exist_ok=True)

        viz.render_variable_graph_labeled(
            before_variables,
            before_report,
            f"outputs/debug/variable_before_iter{iteration}"
        )

        pre_registry_builder = SystemRegistryBuilder(self.variables)
        pre_system_registry = pre_registry_builder.build()

        pre_system_registry["functions"] = self.enricher.enrich(pre_system_registry["functions"])
        pre_registry_builder.save(f"outputs/registry_pre_iter_{iteration}.json")
        pre_registry_builder.save_functions(f"outputs/functions_pre_iter_{iteration}.json")
        print("YAMLs loaded.")

        print("Detection complete.")

        # ITERATIVE REPAIR LOOP

        repair_engine = RepairEngine(self.variables)
        patcher = YAMLPatcher(self.yaml_directory)
        logger = RepairLogger()

        repair_engine.variables = self.variables
        plan = repair_engine.generate_plan(self.report, self.variables, pre_system_registry)

        # Step 1: Parse ONLY LLM actions
        parser = SuggestionParser()
        parsed_llm_actions = parser.parse(plan.actions)
        print("\n[DEBUG] LLM ACTIONS AFTER PARSE:")
        for a in parsed_llm_actions[:10]:
            print(a.action, a.target)
        system_registry = pre_system_registry

        # Step 2: Add flow actions AFTER parsing
        flow_reasoner = FlowReasoner(system_registry)
        flow_actions = flow_reasoner.generate_actions()
        unused_vars = self.report.get("unused_outputs", [])
        unused_reasoner = UnusedOutputReasoner(self.variables, system_registry)
        unused_actions = unused_reasoner.generate_actions(unused_vars)
        unused_repair_actions = []

        for a in unused_actions:
            if not a.get("target"):
                continue

            unused_repair_actions.append(
                RepairAction(
                    action=a["action"],
                    target=a["target"],
                    details=a.get("details", {})
                )
            )
        print("\n[DEBUG] FLOW ACTIONS:")
        for a in flow_actions[:10]:
            print(a)
        flow_repair_actions = [
            RepairAction(
                action=act["action"],
                target=act["target"],
                details=act["details"]
            )
            for act in flow_actions
        ]

        all_actions = deduplicate(parsed_llm_actions + flow_repair_actions + unused_repair_actions)
        print("\n[DEBUG] ALL ACTIONS (BEFORE VALIDATION):")
        for a in all_actions[:15]:
            print(a.action, a.target)

        # Step 3: Validate all
        validator = ActionValidator(self.variables)
        validated_actions = validator.validate(all_actions)
        print("\n[DEBUG] VALIDATED ACTIONS:")
        for a in validated_actions[:15]:
            print(a.action, a.target)

        plan.actions = validated_actions

        if not plan.actions:
            print("[REPAIR] No actions suggested by LLM.")
        else:
            logger.save(plan, iteration=iteration)

            print("Repair Plan:")
            for action in plan.actions:
                print(f"  - {action.action} → {action.target}")

            patcher.apply_plan(plan)
            print("Repair applied.")

            # RELOAD updated YAMLs
            self.load(iteration)
            self.detect()
            self.build_links()

        # SAVE POST-REPAIR REGISTRY
        viz = GraphVisualizer(self.graph)
        viz.render_variable_graph_labeled(
            self.variables,
            self.report,
            "outputs/debug/variable_after"
        )
        viz.render_broken_flows(
            self.variables,
            self.report,
            "outputs/debug/broken_flows"
        )
        post_registry_builder = SystemRegistryBuilder(self.variables)
        post_system_registry = post_registry_builder.build()

        # enrich (will use cache, not LLM repeatedly)
        post_system_registry["functions"] = self.enricher.enrich(post_system_registry["functions"])

        # save enriched registry
        with open(f"outputs/registry_post_iter_{iteration}.json", "w") as f:
            import json
            json.dump(post_system_registry, f, indent=2)

        post_registry_builder.save_functions(f"outputs/functions_post_iter_{iteration}.json")
        print("Repair complete.")
        print("Linking complete.")

        self.report_results()
        print("Generating graph visualization...")

        os.makedirs("outputs", exist_ok=True)

        # Function flow
        viz.render_function_graph("outputs/function_graph")
        # Variable flow (with issues)
        viz.render_variable_graph(self.variables, self.report, "outputs/variable_graph")

        print("\n=== INTEGRATION ENGINE END ===\n")

    # OPTIONAL: Get raw data

    def get_results(self) -> Dict:
        return {
            "variables": self.variables,
            "report": self.report,
            "links": self.links,
            "graph": self.graph
        }