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
        for command in ("bash", "grep", "dirname", "jq"):
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
elif arguments[:3] in (["tx", "tokenfactory", "set-denom-metadata"], ["tx", "tokenfactory", "create-denom"]):
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
        return self.run_action("set-metadata", script=script, **environment)

    def run_action(self, action, script=NORMAL_SCRIPT, **environment):
        return subprocess.run(
            ["/bin/bash", str(script), action], cwd=self.directory,
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
        symbol = settings.get("TOKEN_SYMBOL") or "MTK"
        decimals = int(settings.get("TOKEN_DECIMALS") or "6")
        display = settings.get("TOKEN_DISPLAY") or (symbol if decimals else denom)
        transactions = self.metadata_transactions()
        self.assertEqual(len(transactions), 1)
        arguments = transactions[0][3:]
        self.assertEqual(arguments[:7], [
            settings.get("TOKEN_DESCRIPTION", "My Token Description"), denom, display,
            settings.get("TOKEN_NAME") or "My Token", symbol,
            settings.get("TOKEN_URI", ""), settings.get("TOKEN_URI_HASH", ""),
        ])
        units = [{"denom": denom, "exponent": 0, "aliases": []}]
        if display != denom:
            units.append({"denom": display, "exponent": decimals, "aliases": []})
        self.assertEqual(json.loads(arguments[7]), units)
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
        for action in ("set-metadata", "create-denom"):
            with self.subTest(action=action):
                result = self.run_action(action)
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

    def test_custom_metadata_is_preserved_in_both_help_modes(self):
        settings = {
            "TOKEN_NAME": '研究用 "Token" \\ name',
            "TOKEN_SYMBOL": '研究"T\\K',
            "TOKEN_DESCRIPTION": '説明 "quoted"\n次の行 \\ end',
            "TOKEN_DISPLAY": '表示"単位\\unit',
            "TOKEN_DECIMALS": "8",
            "TOKEN_URI": 'https://example.invalid/metadata?token="研究"&version=1',
            "TOKEN_URI_HASH": 'hash"with\\escapes',
        }
        for usage, ending in ((TEN_ARGUMENT_USAGE, ["8", "false"]), (NINE_ARGUMENT_USAGE, ["8"])):
            with self.subTest(ending=ending):
                if self.log.exists():
                    self.log.unlink()
                result = self.run_metadata(MOCK_USAGE=usage, **settings)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_metadata_arguments(ending, **settings)

    def test_display_defaults_to_custom_symbol(self):
        settings = {"TOKEN_SYMBOL": "LAB", "TOKEN_DECIMALS": "9"}
        result = self.run_metadata(**settings)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_metadata_arguments(["9", "false"], **settings)

    def test_empty_description_is_preserved_while_required_values_default(self):
        settings = {
            "TOKEN_NAME": "", "TOKEN_SYMBOL": "", "TOKEN_DESCRIPTION": "",
            "TOKEN_DISPLAY": "", "TOKEN_DECIMALS": "", "TOKEN_URI": "", "TOKEN_URI_HASH": "",
        }
        result = self.run_metadata(**settings)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_metadata_arguments(["6", "false"], **settings)

    def test_zero_decimals_defaults_to_the_base_denom_with_one_unit(self):
        settings = {"TOKEN_DECIMALS": "0"}
        for usage, ending in ((TEN_ARGUMENT_USAGE, ["0", "false"]), (NINE_ARGUMENT_USAGE, ["0"])):
            with self.subTest(ending=ending):
                if self.log.exists():
                    self.log.unlink()
                result = self.run_metadata(MOCK_USAGE=usage, **settings)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_metadata_arguments(ending, **settings)
                arguments = self.metadata_transactions()[0][3:]
                self.assertEqual(arguments[2], "factory/inj1mockcreator/mtk")
                self.assertEqual(len(json.loads(arguments[7])), 1)

    def test_explicit_base_display_with_positive_decimals_has_one_unit(self):
        settings = {"TOKEN_DISPLAY": "factory/inj1mockcreator/mtk", "TOKEN_DECIMALS": "8"}
        result = self.run_metadata(**settings)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_metadata_arguments(["8", "false"], **settings)
        self.assertEqual(json.loads(self.metadata_transactions()[0][10]), [
            {"denom": "factory/inj1mockcreator/mtk", "exponent": 0, "aliases": []},
        ])

    def test_zero_decimals_with_a_different_display_never_sends_metadata(self):
        result = self.run_metadata(TOKEN_DECIMALS="0", TOKEN_DISPLAY="LAB")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.metadata_transactions(), [])

    def test_invalid_decimals_never_send_a_transaction(self):
        for action in ("create-denom", "set-metadata"):
            for decimals in ("-1", "1.5", "6x", "06", "4294967296"):
                with self.subTest(action=action, decimals=decimals):
                    if self.log.exists():
                        self.log.unlink()
                    result = self.run_action(action, TOKEN_DECIMALS=decimals)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(self.metadata_transactions(), [])
                    self.assertFalse(any(call[:3] == ["tx", "tokenfactory", "create-denom"] for call in self.calls()))

    def test_create_and_metadata_use_their_respective_decimal_limits(self):
        for action, decimals, success in (
            ("create-denom", "0", True), ("create-denom", "24", True),
            ("create-denom", "25", False), ("set-metadata", "25", True),
            ("set-metadata", "4294967295", True),
        ):
            with self.subTest(action=action, decimals=decimals):
                if self.log.exists():
                    self.log.unlink()
                settings = {"TOKEN_DECIMALS": decimals}
                if action == "create-denom" and decimals == "0":
                    settings["TOKEN_DISPLAY"] = "MTK"
                result = self.run_action(action, **settings)
                if success:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    if action == "set-metadata":
                        self.assert_metadata_arguments([decimals, "false"], TOKEN_DECIMALS=decimals)
                    else:
                        writes = [call for call in self.calls() if call[:3] == ["tx", "tokenfactory", "create-denom"]]
                        self.assertEqual(len(writes), 1)
                        self.assertEqual(writes[0][6], decimals)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(any(call[:3] == ["tx", "tokenfactory", "create-denom"] for call in self.calls()))

    def test_create_denom_uses_default_token_metadata(self):
        result = self.run_action("create-denom")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [
            ["keys", "show", "testwallet", "-a", "--keyring-backend", "test"],
            ["tx", "tokenfactory", "create-denom", "mtk", "My Token", "MTK", "6",
             "--from=testwallet", "--keyring-backend", "test", "--chain-id=injective-888",
             "--node=https://injective-testnet-rpc.publicnode.com:443", "--gas-prices=500000000inj",
             "--gas=300000", "-y"],
        ])

    def test_create_denom_and_metadata_share_custom_name_symbol_and_decimals(self):
        settings = {
            "TOKEN_NAME": '研究 "Token"', "TOKEN_SYMBOL": "LAB", "TOKEN_DECIMALS": "8",
            "SUBDENOM": "research", "KEY_NAME": "research wallet", "KEYRING_BACKEND": "file",
        }
        created = self.run_action("create-denom", **settings)
        self.assertEqual(created.returncode, 0, created.stderr)
        creation_calls = [call for call in self.calls() if call[:3] == ["tx", "tokenfactory", "create-denom"]]
        self.assertEqual(len(creation_calls), 1)
        creation_arguments = creation_calls[0][3:]
        self.assertEqual(creation_arguments[:4], ["research", '研究 "Token"', "LAB", "8"])
        self.assertEqual(creation_arguments[4:], [
            "--from=research wallet", "--keyring-backend", "file", "--chain-id=injective-888",
            "--node=https://injective-testnet-rpc.publicnode.com:443", "--gas-prices=500000000inj",
            "--gas=300000", "-y",
        ])
        configured = self.run_metadata(**settings)
        self.assertEqual(configured.returncode, 0, configured.stderr)
        self.assert_metadata_arguments(["8", "false"], **settings)
        metadata_arguments = self.metadata_transactions()[0][3:]
        self.assertEqual(creation_arguments[1:4], [metadata_arguments[3], metadata_arguments[4], metadata_arguments[8]])


if __name__ == "__main__":
    unittest.main()
