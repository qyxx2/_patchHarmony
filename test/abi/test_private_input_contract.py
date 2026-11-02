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
