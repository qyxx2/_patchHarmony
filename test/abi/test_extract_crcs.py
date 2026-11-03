import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "device/abi/extract_crcs.py"
FIXTURES = Path(__file__).parent / "fixtures"
TARGET = "6.1.145-android14-11-maybe-dirty SMP preempt mod_unload modversions aarch64 vivo"


def run_tool(symbols, modules, output):
    return subprocess.run(["python3", str(TOOL), "--symbols", str(symbols), "--module-index", str(modules), "--vermagic", TARGET, "--output-dir", str(output)], text=True, capture_output=True)


class ExtractCrcsTest(unittest.TestCase):
    def test_filters_target_modules_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out"
            result = run_tool(FIXTURES / "symbol-crcs.tsv", FIXTURES / "module-index.tsv", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            with (output / "known-crcs.tsv").open() as handle:
                self.assertEqual([row["symbol"] for row in csv.DictReader(handle, delimiter="\t")], ["alpha", "beta"])
            manifest = json.loads((output / "input-manifest.json").read_text())
            self.assertEqual(manifest["module_count"], 1)
            self.assertEqual(manifest["unique_symbol_count"], 2)

    def test_rejects_conflicting_crc_for_one_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_tool(FIXTURES / "symbol-crcs-conflict.tsv", FIXTURES / "module-index.tsv", Path(tmp) / "out")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("conflicting CRC", result.stderr)

    def test_rejects_missing_required_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            symbols = Path(tmp) / "bad.tsv"
            symbols.write_text("symbol\tcrc\nalpha\t0x1\n")
            result = run_tool(symbols, FIXTURES / "module-index.tsv", Path(tmp) / "out")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("header", result.stderr)
