"""Check TokenFactory metadata compatibility using a mock CLI; never send transactions."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
NORMAL_SCRIPT = ROOT / "setup/normal/07-tokenfactory-mtk.sh"
MACBOOK_SCRIPT = ROOT / "setup/macbook/07-tokenfactory-mtk.sh"
USAGE_PREFIX = (
    "Usage:\n  injectived tx tokenfactory set-denom-metadata "
    "[description] [base] [display] [name] [symbol] [uri] [uri-hash] [denom-units] "
)
TEN_ARGUMENT_USAGE = USAGE_PREFIX + "[decimals] [shouldDisableAdminBurn] [flags]\n"
NINE_ARGUMENT_USAGE = USAGE_PREFIX + "[decimals] [flags]\n"
NINE_ARGUMENT_USAGE_WITHOUT_FLAGS = USAGE_PREFIX + "[decimals]\n"


class TokenFactoryMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sus-bc2-tokenfactory-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.binary_directory = self.directory / "bin"
        self.binary_directory.mkdir()
        self.log = self.directory / "calls.jsonl"
        # No host PATH fallback: injectived must always be the local mock.
        for command in ("bash", "grep", "dirname"):
            executable = shutil.which(command)
            if executable is None:
                self.fail(f"Required test utility is unavailable: {command}")
            (self.binary_directory / command).symlink_to(executable)
        mock = self.binary_directory / "injectived"
        mock.write_text(f"#!{sys.executable}\n" + '''
import json
import os
import sys

arguments = sys.argv[1:]
with open(os.environ["MOCK_LOG"], "a") as stream:
    stream.write(json.dumps(arguments) + "\\n")
if arguments[:2] == ["keys", "show"]:
    print(os.environ["MOCK_CREATOR_ADDR"])
elif arguments == ["tx", "tokenfactory", "set-denom-metadata", "--help"]:
    print(os.environ["MOCK_USAGE"])
    status = int(os.environ.get("MOCK_HELP_STATUS", "0"))
    if status:
        print("mock help failure", file=sys.stderr)
    sys.exit(status)
elif arguments[:3] == ["tx", "tokenfactory", "set-denom-metadata"]:
    status = int(os.environ.get("MOCK_TX_STATUS", "0"))
    if status:
        print("mock transaction failure", file=sys.stderr)
    else:
        print("mock metadata transaction")
    sys.exit(status)
else:
    print("Unexpected mock CLI call", file=sys.stderr)
    sys.exit(99)
''')
        mock.chmod(0o755)
        self.environment = {
            "PATH": str(self.binary_directory),
            "HOME": str(self.directory),
            "MOCK_LOG": str(self.log),
            "MOCK_USAGE": TEN_ARGUMENT_USAGE,
            "MOCK_CREATOR_ADDR": "inj1mockcreator",
            "CONFIRM_TX": "yes",
        }

    def run_metadata(self, script=NORMAL_SCRIPT, **environment):
        return subprocess.run(
            ["/bin/bash", str(script), "set-metadata"], cwd=self.directory,
            env={**self.environment, **environment},
            capture_output=True, text=True, timeout=15,
        )

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def metadata_transactions(self):
        return [
            call for call in self.calls()
            if call[:3] == ["tx", "tokenfactory", "set-denom-metadata"]
            and call[3:] != ["--help"]
        ]

    def assert_metadata_arguments(self, ending, **settings):
        key_name = settings.get("KEY_NAME", "testwallet")
        backend = settings.get("KEYRING_BACKEND", "test")
        subdenom = settings.get("SUBDENOM", "mtk")
        creator = settings.get("MOCK_CREATOR_ADDR", "inj1mockcreator")
        denom = f"factory/{creator}/{subdenom}"
        transactions = self.metadata_transactions()
        self.assertEqual(len(transactions), 1)
        arguments = transactions[0][3:]
        self.assertEqual(arguments[:7], [
            "My Token Description", denom, "MTK", "My Token", "MTK", "", "",
        ])
        self.assertEqual(json.loads(arguments[7]), [
            {"denom": denom, "exponent": 0, "aliases": []},
            {"denom": "MTK", "exponent": 6, "aliases": []},
        ])
        self.assertEqual(arguments[8:8 + len(ending)], ending)
        self.assertEqual(arguments[8 + len(ending):], [
            f"--from={key_name}", "--keyring-backend", backend,
            f'--chain-id={settings.get("CHAIN_ID", "injective-888")}',
            f'--node={settings.get("NODE", "https://injective-testnet-rpc.publicnode.com:443")}',
            f'--gas-prices={settings.get("GAS_PRICES", "500000000inj")}',
            f'--gas={settings.get("GAS", "300000")}', "-y",
        ])
        self.assertIn(["keys", "show", key_name, "-a", "--keyring-backend", backend], self.calls())
        help_call = ["tx", "tokenfactory", "set-denom-metadata", "--help"]
        self.assertEqual(self.calls().count(help_call), 1)
        self.assertLess(self.calls().index(help_call), self.calls().index(transactions[0]))

    def test_ten_argument_usage_selects_six_and_false(self):
        result = self.run_metadata()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_metadata_arguments(["6", "false"])

    def test_nine_argument_usage_selects_six_only(self):
        result = self.run_metadata(MOCK_USAGE=NINE_ARGUMENT_USAGE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_metadata_arguments(["6"])

    def test_nine_argument_usage_without_flags_is_supported(self):
        result = self.run_metadata(MOCK_USAGE=NINE_ARGUMENT_USAGE_WITHOUT_FLAGS)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_metadata_arguments(["6"])

    def test_unknown_usage_never_sends_metadata(self):
        usage = USAGE_PREFIX + "[decimals] [futureArgument] [flags]\n"
        result = self.run_metadata(MOCK_USAGE=usage)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.metadata_transactions(), [])
        self.assertIn("Usage", result.stderr)

    def test_help_failure_keeps_status_and_never_sends_metadata(self):
        result = self.run_metadata(MOCK_HELP_STATUS="23")
        self.assertEqual(result.returncode, 23)
        self.assertIn("mock help failure", result.stderr)
        self.assertEqual(self.metadata_transactions(), [])

    def test_missing_confirmation_prevents_all_cli_calls(self):
        self.environment.pop("CONFIRM_TX")
        result = self.run_metadata()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONFIRM_TX=yes", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_transaction_failure_keeps_original_status(self):
        result = self.run_metadata(MOCK_TX_STATUS="42")
        self.assertEqual(result.returncode, 42)
        self.assertIn("mock transaction failure", result.stderr)
        self.assert_metadata_arguments(["6", "false"])

    def test_custom_key_denom_and_flags_are_preserved(self):
        settings = {
            "KEY_NAME": "research wallet", "KEYRING_BACKEND": "file",
            "SUBDENOM": "research", "MOCK_CREATOR_ADDR": "inj1othermockcreator",
            "CHAIN_ID": "custom-chain", "NODE": "https://rpc.example.invalid:443",
            "GAS_PRICES": "700000000inj", "GAS": "450000",
        }
        result = self.run_metadata(**settings)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_metadata_arguments(["6", "false"], **settings)

    def test_macbook_wrapper_uses_compatible_metadata_arguments(self):
        result = self.run_metadata(script=MACBOOK_SCRIPT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_metadata_arguments(["6", "false"])


if __name__ == "__main__":
    unittest.main()
