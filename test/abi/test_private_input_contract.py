import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PrivateInputContractTest(unittest.TestCase):
    def test_workflow_is_manual_and_sanitized(self):
        workflow = (ROOT / ".github/workflows/pd2307-abi.yml").read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("push:", workflow)
        self.assertIn("ghcr.io/ylarod/ddk-min:android14-6.1-20260313", workflow)
        self.assertIn("reports/", workflow)
        self.assertNotIn("private/", workflow)

    def test_runner_verifies_before_decrypting(self):
        runner = (ROOT / "device/abi/run-private-input.sh").read_text()
        self.assertIn("sha256sum -c", runner)
        self.assertLess(runner.index("sha256sum -c"), runner.index("openssl enc -d"))
        self.assertIn("trap", runner)
        self.assertIn("--module-index", runner)

    def test_runner_collects_sanitized_ddk_diagnostics(self):
        runner = (ROOT / "device/abi/run-private-input.sh").read_text()
        self.assertIn("ddk-diagnostics.json", runner)
        self.assertIn("genksyms", runner)
        self.assertIn("sha256sum", runner)

    def test_runner_records_genksyms_usage(self):
        runner = (ROOT / "device/abi/run-private-input.sh").read_text()
        self.assertIn("genksyms-usage.txt", runner)
        self.assertIn("--help", runner)

    def test_runner_runs_minimal_known_symbol_probe(self):
        runner = (ROOT / "device/abi/run-private-input.sh").read_text()
        self.assertIn("__stack_chk_fail", runner)
        self.assertIn("genksyms-probe.txt", runner)
        self.assertIn(" -D ", runner)


class PrivateInputDocumentationTest(unittest.TestCase):
    def test_readme_names_all_required_secrets_and_boundary(self):
        text = (ROOT / "device/abi/README.md").read_text()
        for name in ["PD2307_INPUT_URL", "PD2307_INPUT_SHA256", "PD2307_INPUT_PASSPHRASE", "PD2307_INPUT_TOKEN"]:
            self.assertIn(name, text)
        self.assertIn("workflow_dispatch", text)
        self.assertIn("does not build or load", text)
