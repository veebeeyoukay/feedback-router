#!/usr/bin/env python3
"""
Seed test data through the feedback-router pipeline.

This script loads all test fixtures and demonstrates how they would flow
through the full pipeline (input → normalization → classification → routing).

Usage:
    python scripts/seed_data.py
    python scripts/seed_data.py --verbose
    python scripts/seed_data.py --fixture prospect_productivity.json
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict
import argparse
from datetime import datetime

# Add src to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


class FeedbackPipelineSimulator:
    """Simulates the feedback pipeline for testing and seeding."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = []

    def load_fixture(self, fixture_path: Path) -> Dict[str, Any]:
        """Load a fixture from JSON file."""
        with open(fixture_path) as f:
            return json.load(f)

    def simulate_pipeline(self, fixture: Dict[str, Any], fixture_name: str) -> Dict[str, Any]:
        """
        Simulate the full pipeline for a fixture.

        Pipeline stages:
        1. Intake: Normalize raw input
        2. Classification: Analyze and tag
        3. Routing: Decide action and team
        4. Response: Generate response metadata
        """
        result = {
            "fixture": fixture_name,
            "timestamp": datetime.now().isoformat(),
            "stages": {},
        }

        # Stage 1: Intake
        if self.verbose:
            print(f"  [1/4] Intake...")
        result["stages"]["intake"] = {
            "status": "success",
            "raw_input": fixture["raw_input"][:50] + "..."
            if len(fixture["raw_input"]) > 50
            else fixture["raw_input"],
            "channel": fixture["channel"],
            "contact_name": fixture["metadata"]["contact"]["name"],
        }

        # Stage 2: Classification
        if self.verbose:
            print(f"  [2/4] Classification...")
        classification = fixture["expected_classification"]
        result["stages"]["classification"] = {
            "status": "success",
            "category": classification["category"],
            "contact_type": classification["contact_type"],
            "themes": classification["themes"],
            "sentiment": classification["sentiment"],
            "urgency": classification["urgency"],
            "icp_fit": classification.get("icp_fit", "unknown"),
        }

        # Stage 3: Routing
        if self.verbose:
            print(f"  [3/4] Routing...")
        routing = fixture["expected_routing"]
        result["stages"]["routing"] = {
            "status": "success",
            "action": routing["action"],
            "team": routing["team"],
            "escalated": routing["escalated"],
            "reason": routing["reason"],
        }

        # Stage 4: Response generation
        if self.verbose:
            print(f"  [4/4] Response generation...")
        result["stages"]["response"] = {
            "status": "success",
            "response_type": (
                "concierge" if routing["team"] == "concierge" else "routing"
            ),
            "handler": routing["team"],
        }

        result["overall_status"] = "success"
        return result

    def seed_all_fixtures(self) -> None:
        """Load and process all fixtures."""
        if not FIXTURES_DIR.exists():
            print(f"Error: Fixtures directory not found at {FIXTURES_DIR}")
            sys.exit(1)

        fixture_files = sorted(FIXTURES_DIR.glob("*.json"))
        if not fixture_files:
            print(f"No fixtures found in {FIXTURES_DIR}")
            sys.exit(1)

        print(f"Found {len(fixture_files)} fixtures")
        print("")

        for i, fixture_path in enumerate(fixture_files, 1):
            fixture_name = fixture_path.name
            print(f"[{i}/{len(fixture_files)}] Processing {fixture_name}")

            try:
                fixture = self.load_fixture(fixture_path)
                result = self.simulate_pipeline(fixture, fixture_name)
                self.results.append(result)

                # Print summary for this fixture
                intake = result["stages"]["intake"]
                classification = result["stages"]["classification"]
                routing = result["stages"]["routing"]

                print(f"  ✓ Contact: {intake['contact_name']}")
                print(
                    f"  ✓ Category: {classification['category']} | Themes: {classification['themes']}"
                )
                print(f"  ✓ Team: {routing['team']} | Escalated: {routing['escalated']}")

                if self.verbose:
                    print(f"  ✓ Reason: {routing['reason'][:60]}...")

                print("")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                result = {
                    "fixture": fixture_name,
                    "timestamp": datetime.now().isoformat(),
                    "overall_status": "error",
                    "error": str(e),
                }
                self.results.append(result)
                print("")

    def print_summary(self) -> None:
        """Print summary of seeded data."""
        print("=" * 60)
        print("SEEDING SUMMARY")
        print("=" * 60)
        print("")

        successful = [r for r in self.results if r.get("overall_status") == "success"]
        failed = [r for r in self.results if r.get("overall_status") == "error"]

        print(f"Total fixtures: {len(self.results)}")
        print(f"✓ Successful: {len(successful)}")
        print(f"✗ Failed: {len(failed)}")
        print("")

        if successful:
            print("Successful Fixtures:")
            for result in successful:
                print(f"  ✓ {result['fixture']}")

        if failed:
            print("")
            print("Failed Fixtures:")
            for result in failed:
                print(f"  ✗ {result['fixture']}: {result.get('error')}")

        print("")
        print("=" * 60)
        print("Statistics by Classification")
        print("=" * 60)
        print("")

        categories = {}
        teams = {}
        themes_count = {}

        for result in successful:
            if "classification" not in result["stages"]:
                continue
            classification = result["stages"]["classification"]
            routing = result["stages"]["routing"]

            # Count categories
            category = classification["category"]
            categories[category] = categories.get(category, 0) + 1

            # Count teams
            team = routing["team"]
            teams[team] = teams.get(team, 0) + 1

            # Count themes
            for theme in classification["themes"]:
                themes_count[theme] = themes_count.get(theme, 0) + 1

        print("Categories:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")

        print("")
        print("Teams:")
        for team, count in sorted(teams.items()):
            print(f"  {team}: {count}")

        print("")
        print("Themes (by frequency):")
        theme_names = {
            1: "Workplace Productivity",
            2: "Career Security",
            3: "Learning Curve",
            4: "Privacy & Safety",
            5: "Family & Personal Life",
        }
        for theme_num in sorted(themes_count.keys()):
            count = themes_count[theme_num]
            name = theme_names.get(theme_num, f"Theme {theme_num}")
            print(f"  {theme_num}. {name}: {count}")

        print("")

    def save_results(self, output_path: Path | None = None) -> None:
        """Save seeding results to JSON file."""
        if output_path is None:
            output_path = (
                PROJECT_ROOT / "data" / f"seeding_results_{datetime.now():%Y%m%d_%H%M%S}.json"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"Results saved to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed test data through the feedback router pipeline"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--fixture", help="Process a specific fixture (e.g., prospect_productivity.json)"
    )
    parser.add_argument(
        "--save", "-s", action="store_true", help="Save results to JSON file"
    )

    args = parser.parse_args()

    print("")
    print("=" * 60)
    print("Feedback Router - Data Seeding Script")
    print("=" * 60)
    print("")

    simulator = FeedbackPipelineSimulator(verbose=args.verbose)

    if args.fixture:
        # Process specific fixture
        fixture_path = FIXTURES_DIR / args.fixture
        if not fixture_path.exists():
            print(f"Error: Fixture not found: {fixture_path}")
            sys.exit(1)

        print(f"Processing fixture: {args.fixture}")
        print("")

        try:
            fixture = simulator.load_fixture(fixture_path)
            result = simulator.simulate_pipeline(fixture, args.fixture)
            simulator.results.append(result)

            print("Stages:")
            for stage_name, stage_result in result["stages"].items():
                status_icon = "✓" if stage_result.get("status") == "success" else "✗"
                print(f"  {status_icon} {stage_name}")

            print("")
            print("Details:")
            for stage_name, stage_result in result["stages"].items():
                print(f"  {stage_name}:")
                for key, value in stage_result.items():
                    if key != "status":
                        print(f"    {key}: {value}")

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    else:
        # Process all fixtures
        simulator.seed_all_fixtures()

    # Print summary
    print("")
    simulator.print_summary()

    # Optionally save results
    if args.save:
        simulator.save_results()

    print("✓ Seeding complete!")
    print("")


if __name__ == "__main__":
    main()
