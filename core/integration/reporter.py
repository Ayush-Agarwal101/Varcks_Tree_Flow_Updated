# core/integration/reporter.py

from typing import Dict, List

class IntegrationReporter:
    """
    Formats and prints integration analysis results.
    """

    def __init__(self, report: Dict, links: List[Dict], graph: Dict[str, List[str]]):
        self.report = report
        self.links = links
        self.graph = graph

    # ERROR REPORTING

    def print_errors(self):
        print("\n==============================")
        print(" INTEGRATION ERROR REPORT")
        print("==============================\n")

        # Missing Producers
        missing = self.report.get("missing_producers", [])
        print("❌ MISSING PRODUCERS:")
        if missing:
            for var in missing:
                print(f"  - {var}")
        else:
            print("  ✓ None")
        print()

        # Multiple Producers
        multiple = self.report.get("multiple_producers", [])
        print("⚠️ MULTIPLE PRODUCERS:")
        if multiple:
            for var, producers in multiple:
                print(f"  - {var}")
                for p in producers:
                    print(f"      produced by → {p}")
        else:
            print("  ✓ None")
        print()

        # Type Conflicts
        conflicts = self.report.get("type_conflicts", [])
        print("⚠️ TYPE CONFLICTS:")
        if conflicts:
            for var, types in conflicts:
                print(f"  - {var}: {types}")
        else:
            print("  ✓ None")
        print()

        # Unused Outputs
        unused = self.report.get("unused_outputs", [])
        print("⚠️ UNUSED OUTPUTS:")
        if unused:
            for var in unused:
                print(f"  - {var}")
        else:
            print("  ✓ None")
        print()

    # LINK REPORT

    def print_links(self):
        print("\n==============================")
        print(" VARIABLE FLOW LINKS")
        print("==============================\n")

        if not self.links:
            print("No links found.\n")
            return

        for link in self.links:
            print(f"{link['from']}  --[{link['variable']}]-->  {link['to']}")

        print()

    # FUNCTION GRAPH

    def print_function_graph(self):
        print("\n==============================")
        print(" FUNCTION DEPENDENCY GRAPH")
        print("==============================\n")

        if not self.graph:
            print("Graph is empty.\n")
            return

        for fn, deps in self.graph.items():
            if deps:
                print(f"{fn} → {deps}")
            else:
                print(f"{fn} → []")

        print()

    # SUMMARY

    def print_summary(self):
        print("\n==============================")
        print(" SUMMARY")
        print("==============================\n")

        total_vars = len(self.report.get("missing_producers", [])) + \
                     len(self.report.get("multiple_producers", [])) + \
                     len(self.report.get("type_conflicts", [])) + \
                     len(self.report.get("unused_outputs", []))

        print(f"Total issues detected: {total_vars}")
        print("Check sections above for details.\n")