"""Check SimBlock aggregation with temporary synthetic files, never a simulation."""

import csv
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "Day3/calc_simblock_propagation.sh"
WRAPPERS = [ROOT / "Day3/calc_simblock_metrics.sh", ROOT / "Day3/renew_calc_simblock_metrics.sh"]
CSV_NAME = "propagation_metrics_from_add_block.csv"
CSV_FIELDS = [
    "block_id", "generation_time", "reached_nodes", "reached_rate",
    "avg_time", "p90_time", "p95_time", "max_time",
]
FULL_AVERAGES = [
    "full_reach_average_block_propagation_time",
    "full_reach_average_90pct_node_arrival_time",
    "full_reach_average_95pct_node_arrival_time",
]


def node(node_id):
    return {"kind": "add-node", "content": {"node-id": node_id}}


def arrival(block_id, node_id, timestamp):
    return {"kind": "add-block", "content": {
        "block-id": block_id, "node-id": node_id, "timestamp": timestamp,
    }}


class SimBlockMetricsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sus-bc2-simblock-metrics-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.output = self.directory / "output with spaces"
        self.output.mkdir()
        self.home = self.directory / "home"
        self.home.mkdir()
        self.binary_directory = self.directory / "bin"
        self.binary_directory.mkdir()
        # Only the interpreter and wrapper utilities exist on PATH.
        for name, executable in (
            ("python3", str(Path(sys.executable).resolve())),
            ("bash", "/bin/bash"), ("dirname", shutil.which("dirname")),
        ):
            self.assertIsNotNone(executable, f"Required test utility unavailable: {name}")
            (self.binary_directory / name).symlink_to(executable)
        self.environment = {
            "PATH": str(self.binary_directory), "HOME": str(self.home),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        self.write_block_list("OnChain : 1 : 101\nOrphan : 1 : 102\nOnChain : 300 : 103\n")
        self.write_events([node(1), node(2), arrival(101, 1, 100), arrival(101, 2, 110)])

    def write_block_list(self, text):
        (self.output / "blockList.txt").write_text(text, encoding="utf-8")

    def write_events(self, events):
        (self.output / "output.json").write_text(json.dumps(events), encoding="utf-8")

    def run_metrics(self, *, entry=ENTRY, environment=None, output=True):
        command = ["/bin/bash", str(entry)]
        if output:
            command.append(str(self.output))
        result = subprocess.run(
            command, cwd=self.directory, env={**self.environment, **(environment or {})},
            capture_output=True, text=True, timeout=15,
        )
        values = {}
        for line in result.stdout.splitlines():
            match = re.match(r"^\s*([a-z][a-z0-9_]*)\s*[:=]\s*(.*?)\s*$", line)
            if match:
                values[match.group(1)] = match.group(2)
        return result, values

    def read_rows(self, output=None):
        with ((output or self.output) / CSV_NAME).open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(reader.fieldnames, CSV_FIELDS)
            return list(reader)

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_metric(self, values, key, expected, delta=0.000001):
        self.assertIn(key, values)
        self.assertAlmostEqual(float(values[key].rstrip("%")), expected, delta=delta, msg=key)

    def assert_full_reach_unavailable(self, values):
        self.assertEqual(values["full_reach_propagation_available"], "0")
        for key in FULL_AVERAGES:
            self.assertEqual(values[key], "N/A", key)

    def test_counts_ignore_blank_lines_and_height_300_is_not_the_denominator(self):
        self.write_block_list("\nOnChain : 1 : 101\n\nOrphan : 1 : 102\n  \nOnChain : 300 : 103")
        result, values = self.run_metrics()
        self.assert_success(result)
        for key, expected in (
            ("onchain_blocks", 2), ("orphan_blocks", 1),
            ("all_generated_blocks", 3), ("fork_count", 1),
        ):
            self.assert_metric(values, key, expected)
        self.assert_metric(values, "fork_rate", 1 / 3)
        self.assert_metric(values, "orphan_rate", 1 / 3)
        self.assertTrue(values["fork_rate_percent"].endswith("%"))
        self.assert_metric(values, "fork_rate_percent", 100 / 3, delta=0.01)
        self.assert_metric(values, "interval_sec", 600)
        self.assert_metric(values, "tx_per_block", 4000)
        self.assert_metric(values, "estimated_sim_time_sec", 1200)
        self.assert_metric(values, "effective_tps_onchain", 4000 / 600, delta=0.01)
        self.assert_metric(values, "generated_block_tps", 10, delta=0.01)

        result, values = self.run_metrics(environment={"BLOCK_SIZE": "1200", "AVG_TX_SIZE": "100", "INTERVAL_SEC": "20"})
        self.assert_success(result)
        self.assert_metric(values, "tx_per_block", 12)
        self.assert_metric(values, "estimated_sim_time_sec", 40)
        self.assert_metric(values, "effective_tps_onchain", 0.6)
        self.assert_metric(values, "tps_from_interval", 0.6)
        self.assert_metric(values, "generated_block_tps", 0.9)

    def test_complete_and_partial_blocks_have_separate_averages_in_milliseconds(self):
        self.write_events([
            *[node(index) for index in range(1, 5)],
            arrival(11, 4, 1040), arrival(11, 2, 1010), arrival(11, 1, 1000), arrival(11, 3, 1020),
            arrival(22, 1, 2000), arrival(22, 2, 2030),
        ])
        result, values = self.run_metrics()
        self.assert_success(result)
        self.assertEqual(values["propagation_time_unit"], "milliseconds")
        self.assertEqual(values["propagation_available"], "1")
        self.assertEqual(values["full_reach_propagation_available"], "1")
        for key, expected in (
            ("num_nodes", 4), ("parsed_blocks", 2), ("fully_reached_blocks", 1), ("partially_reached_blocks", 1),
            ("average_block_propagation_time", 16.25),
            ("average_90pct_node_arrival_time", 35), ("average_95pct_node_arrival_time", 35),
            ("average_max_node_arrival_time", 35),
            (FULL_AVERAGES[0], 17.5), (FULL_AVERAGES[1], 40), (FULL_AVERAGES[2], 40),
        ):
            self.assert_metric(values, key, expected)
        rows = self.read_rows()
        self.assertEqual([int(row["block_id"]) for row in rows], [11, 22])
        self.assertEqual([int(row["reached_nodes"]) for row in rows], [4, 2])
        self.assertEqual([float(row["reached_rate"]) for row in rows], [100, 50])
        self.assertEqual([float(row["generation_time"]) for row in rows], [1000, 2000])
        self.assertEqual([float(row["avg_time"]) for row in rows], [17.5, 15])

    def test_partial_observations_do_not_substitute_for_full_reach_results(self):
        self.write_events([*[node(index) for index in range(4)], arrival(1, 0, 5000), arrival(1, 1, 5250)])
        result, values = self.run_metrics()
        self.assert_success(result)
        self.assertEqual(values["propagation_available"], "1")
        self.assert_metric(values, "average_block_propagation_time", 125)
        self.assert_metric(values, "fully_reached_blocks", 0)
        self.assert_metric(values, "partially_reached_blocks", 1)
        self.assert_full_reach_unavailable(values)

    def test_duplicate_arrivals_keep_the_earliest_timestamp_and_singletons_are_excluded(self):
        self.write_events([
            node(1), node(2), node(3), node(3),
            arrival(7, 1, 300), arrival(7, 2, 200), arrival(7, 3, 400),
            arrival(7, 1, 100), arrival(7, 2, 250), arrival(9, 1, 900),
        ])
        result, values = self.run_metrics()
        self.assert_success(result)
        self.assert_metric(values, "num_nodes", 3)
        self.assert_metric(values, "parsed_blocks", 1)
        row, = self.read_rows()
        self.assertEqual(int(row["block_id"]), 7)
        self.assertEqual(int(row["reached_nodes"]), 3)
        self.assertEqual(float(row["generation_time"]), 100)
        self.assertAlmostEqual(float(row["avg_time"]), 400 / 3, delta=0.000001)
        for field in ("p90_time", "p95_time", "max_time"):
            self.assertEqual(float(row[field]), 300)

    def test_percentiles_use_nearest_rank_and_include_the_generation_node(self):
        self.write_events([
            *[node(index) for index in range(20)],
            *[arrival(8, index, 1000 + index) for index in range(20)],
        ])
        result, values = self.run_metrics()
        self.assert_success(result)
        row, = self.read_rows()
        self.assertEqual(float(row["avg_time"]), 9.5)
        self.assertEqual(float(row["p90_time"]), 17)
        self.assertEqual(float(row["p95_time"]), 18)
        self.assertEqual(float(row["max_time"]), 19)
        self.assert_metric(values, FULL_AVERAGES[1], 17)
        self.assert_metric(values, FULL_AVERAGES[2], 18)

    def test_missing_json_nodes_or_valid_arrivals_report_unavailable_without_full_reach_fallback(self):
        cases = [
            None,
            [arrival(1, 1, 100), arrival(1, 2, 200)],
            [node(1), node(2)],
            [node(1), node(2), arrival(1, 1, 100)],
        ]
        for events in cases:
            with self.subTest(events=events):
                stale_csv = self.output / CSV_NAME
                stale_csv.write_text("previous run must not be reused\n", encoding="utf-8")
                if events is None:
                    (self.output / "output.json").unlink(missing_ok=True)
                else:
                    self.write_events(events)
                result, values = self.run_metrics()
                self.assertEqual(values.get("propagation_available"), "0", result.stdout + result.stderr)
                self.assertTrue(values.get("propagation_error"), result.stdout + result.stderr)
                self.assertIn("effective_tps_onchain", values)
                self.assert_full_reach_unavailable(values)
                self.assertFalse(stale_csv.exists(), "Unavailable input must remove the previous generated CSV")

    def test_malformed_json_fails_with_an_explicit_error(self):
        (self.output / "output.json").write_text("{broken JSON", encoding="utf-8")
        result, _ = self.run_metrics()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ERROR", result.stdout + result.stderr)

    def test_invalid_positive_integer_settings_fail(self):
        for name in ("BLOCK_SIZE", "AVG_TX_SIZE", "INTERVAL_SEC"):
            for value in ("0", "-1", "1.5", "invalid"):
                with self.subTest(name=name, value=value):
                    result, _ = self.run_metrics(environment={name: value})
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("ERROR", result.stdout + result.stderr)

    def test_empty_or_missing_block_list_fails(self):
        for text in ("", "\n  \n\t\n", None):
            with self.subTest(text=text):
                if text is None:
                    (self.output / "blockList.txt").unlink()
                else:
                    self.write_block_list(text)
                result, _ = self.run_metrics()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ERROR", result.stdout + result.stderr)

    def test_legacy_entrypoints_and_simblock_dir_resolve_to_the_same_metrics(self):
        result, expected = self.run_metrics()
        self.assert_success(result)
        expected_csv = (self.output / CSV_NAME).read_text()
        for wrapper in WRAPPERS:
            with self.subTest(wrapper=wrapper.name):
                result, values = self.run_metrics(entry=wrapper)
                self.assert_success(result)
                self.assertEqual(values, expected)
                self.assertEqual((self.output / CSV_NAME).read_text(), expected_csv)

        simulator = self.directory / "simblock with spaces"
        default_output = simulator / "simulator/src/dist/output"
        shutil.copytree(self.output, default_output)
        result, values = self.run_metrics(environment={"SIMBLOCK_DIR": str(simulator)}, output=False)
        self.assert_success(result)
        for key in ("fork_rate", "parsed_blocks", "average_block_propagation_time", *FULL_AVERAGES):
            self.assertEqual(values[key], expected[key])
        self.assertEqual(self.read_rows(default_output), self.read_rows())

    def test_partial_reach_is_never_rounded_to_100_percent(self):
        count = 20001
        self.write_events([
            *[node(index) for index in range(count)],
            *[arrival(1, index, index) for index in range(count - 1)],
        ])
        result, values = self.run_metrics()
        self.assert_success(result)
        row, = self.read_rows()
        self.assertEqual(int(row["reached_nodes"]), count - 1)
        self.assertLess(float(row["reached_rate"]), 100)
        self.assert_metric(values, "fully_reached_blocks", 0)
        self.assert_metric(values, "partially_reached_blocks", 1)
        self.assert_full_reach_unavailable(values)


if __name__ == "__main__":
    unittest.main()
