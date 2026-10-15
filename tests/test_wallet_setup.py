"""Check wallet setup with a mock CLI; never create real keys or transactions."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/injectived/create-test-wallet.sh"


class WalletSetupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sus-bc2-wallet-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.binary_directory = self.directory / "bin"
        self.binary_directory.mkdir()
        self.log = self.directory / "calls.jsonl"
        # PATH is closed: even a missing mock cannot invoke the user's real CLI.
        for command in ("bash", "dirname", "cat"):
            executable = shutil.which(command)
            if executable is None:
                self.fail(f"Required test utility is unavailable: {command}")
            (self.binary_directory / command).symlink_to(executable)
        self.cli = self.binary_directory / "injectived"
        self.cli.write_text(f"#!{sys.executable}\n" + '''
import json
import os
from pathlib import Path
import sys

arguments = sys.argv[1:]
log = Path(os.environ["MOCK_LOG"])
previous = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
with open(os.environ["MOCK_LOG"], "a") as stream:
    stream.write(json.dumps(arguments) + "\\n")
if arguments[:2] == ["keys", "show"]:
    if "-a" in arguments:
        key_name = arguments[2]
        occurrence = 1 + sum(call[:3] == ["keys", "show", key_name] and "-a" in call for call in previous)
        selected = (
            key_name == os.environ.get("MOCK_ADDRESS_TARGET", key_name)
            and occurrence == int(os.environ.get("MOCK_ADDRESS_OCCURRENCE", str(occurrence)))
        )
        status = int(os.environ.get("MOCK_ADDRESS_STATUS", "0"))
        if status and selected:
            print("mock address query failure", file=sys.stderr)
            sys.exit(status)
        addresses = json.loads(os.environ.get("MOCK_ADDRESS_MAP", "{}"))
        address = addresses.get(key_name, os.environ["MOCK_ADDRESS"])
        print("" if os.environ.get("MOCK_EMPTY_ADDRESS") == "yes" and selected else address)
    else:
        sys.exit(0 if os.environ.get("MOCK_KEY_EXISTS") == "yes" else 1)
elif arguments[:2] == ["keys", "add"]:
    status = int(os.environ.get("MOCK_ADD_STATUS", "0"))
    if arguments[2] != os.environ.get("MOCK_ADD_TARGET", arguments[2]):
        status = 0
    if status:
        print("mock wallet creation failure", file=sys.stderr)
    else:
        print("mock wallet created")
    sys.exit(status)
elif arguments[:2] == ["keys", "list"]:
    print("mock key list")
    sys.exit(int(os.environ.get("MOCK_LIST_STATUS", "0")))
else:
    print("Unexpected mock CLI call", file=sys.stderr)
    sys.exit(99)
''')
        self.cli.chmod(0o755)
        self.environment = {
            "PATH": str(self.binary_directory),
            "HOME": str(self.directory),
            "MOCK_LOG": str(self.log),
            "MOCK_ADDRESS": "inj1mockwalletaddress",
        }

    def run_helper(self, *arguments, script=HELPER, **environment):
        if self.log.exists():
            self.log.unlink()
        return subprocess.run(
            ["/bin/bash", str(script), *arguments], cwd=self.directory,
            env={**self.environment, **environment},
            capture_output=True, text=True, timeout=15,
        )

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def run_document_wallet_block(self, *, existing_wallet=False, **environment):
        document = (ROOT / "docs/injective-setup.md").read_text()
        section = re.search(
            r"^## 2\..*?\n(.*?)(?=^<details>|^## |\Z)",
            document, flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(section, "Expected the documented wallet creation section")
        blocks = re.findall(r"^```bash\s*\n(.*?)^```", section.group(1), flags=re.MULTILINE | re.DOTALL)
        self.assertEqual(len(blocks), 1, "Expected one documented wallet creation block")
        block = blocks[0]
        if existing_wallet:
            block, omitted = re.subn(r"^injectived keys add[^\n]*\n", "", block, flags=re.MULTILINE)
            self.assertEqual(omitted, 1, "Existing wallets omit the documented keys add line")
        if self.log.exists():
            self.log.unlink()
        state = '''
printf '\\n__WALLET_DOC_STATE__\\n%s\\n%s\\n%s\\n%s\\n%s\\n' \\
  "$KEY_NAME" "$KEYRING_BACKEND" "$MY_ADDR" "$ADDR" "$RECIPIENT_ADDR"
'''
        return subprocess.run(
            ["/bin/bash", "-u", "-c", block + state], cwd=self.directory,
            env={
                **self.environment,
                # These values represent the settings established in step 1.
                "KEY_NAME": "testwallet", "KEYRING_BACKEND": "test",
                "MY_ADDR": "stale sender", "ADDR": "stale address", "RECIPIENT_ADDR": "stale recipient",
                **environment,
            },
            capture_output=True, text=True, timeout=15,
        )

    def assert_wallet_calls(self, key_name="testwallet", backend="test", existing=False):
        expected = [["keys", "show", key_name, "--keyring-backend", backend]]
        if not existing:
            expected.append(["keys", "add", key_name, "--keyring-backend", backend])
        expected.append(["keys", "show", key_name, "-a", "--keyring-backend", backend])
        self.assertEqual(self.calls(), expected)

    def assert_usable_shell_exports(self, output, key_name="testwallet", backend="test"):
        exports = [line.strip() for line in output.splitlines() if line.strip().startswith("export ")]
        self.assertTrue(exports, "Successful setup must show current-shell export commands")
        result = subprocess.run(
            ["/bin/bash", "-eu", "-c", "\n".join(exports) +
             '\nprintf "%s\\n" "$KEY_NAME" "$KEYRING_BACKEND" "$MY_ADDR"'],
            env={"PATH": str(self.binary_directory), "HOME": str(self.directory)},
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [key_name, backend, self.environment["MOCK_ADDRESS"]])

    def test_unset_key_defaults_to_testwallet_and_creates_missing_key(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_wallet_calls()
        self.assertIn("Wallet is ready.", result.stdout)
        self.assertIn("KEYRING_BACKEND", result.stdout)
        self.assert_usable_shell_exports(result.stdout)

    def test_existing_key_is_reused_without_keys_add(self):
        result = self.run_helper(MOCK_KEY_EXISTS="yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_wallet_calls(existing=True)
        self.assertIn("Wallet already exists", result.stdout)

    def test_nonempty_environment_key_is_used(self):
        result = self.run_helper(KEY_NAME="environment-wallet")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_wallet_calls(key_name="environment-wallet")
        self.assert_usable_shell_exports(result.stdout, key_name="environment-wallet")

    def test_first_argument_takes_precedence_over_environment(self):
        result = self.run_helper("argument-wallet", KEY_NAME="environment-wallet")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_wallet_calls(key_name="argument-wallet")
        self.assert_usable_shell_exports(result.stdout, key_name="argument-wallet")

    def test_explicit_empty_argument_is_rejected_before_cli(self):
        result = self.run_helper("", KEY_NAME="environment-wallet")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("KEY_NAME", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertNotIn("Wallet is ready.", result.stdout)

    def test_empty_environment_key_is_rejected_before_cli(self):
        result = self.run_helper(KEY_NAME="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("KEY_NAME", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertNotIn("Wallet is ready.", result.stdout)

    def test_empty_or_unset_backend_defaults_to_test(self):
        for environment in ({}, {"KEYRING_BACKEND": ""}):
            with self.subTest(environment=environment):
                result = self.run_helper(**environment)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_wallet_calls()
                self.assert_usable_shell_exports(result.stdout)

    def test_custom_backend_and_key_name_survive_current_shell_exports(self):
        result = self.run_helper("research wallet", KEYRING_BACKEND="file")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_wallet_calls(key_name="research wallet", backend="file")
        self.assert_usable_shell_exports(result.stdout, key_name="research wallet", backend="file")

    def test_address_query_failure_keeps_original_status(self):
        result = self.run_helper(MOCK_KEY_EXISTS="yes", MOCK_ADDRESS_STATUS="29")
        self.assertEqual(result.returncode, 29)
        self.assertIn("mock address query failure", result.stderr)
        self.assert_wallet_calls(existing=True)
        self.assertNotIn("Wallet is ready.", result.stdout)

    def test_empty_address_is_rejected(self):
        result = self.run_helper(MOCK_EMPTY_ADDRESS="yes")
        self.assertNotEqual(result.returncode, 0)
        self.assert_wallet_calls()
        self.assertNotIn("Wallet is ready.", result.stdout)

    def test_failed_wallet_creation_stops_before_address_query(self):
        result = self.run_helper(MOCK_ADD_STATUS="42")
        self.assertEqual(result.returncode, 42)
        self.assertIn("mock wallet creation failure", result.stderr)
        self.assertEqual(self.calls(), [
            ["keys", "show", "testwallet", "--keyring-backend", "test"],
            ["keys", "add", "testwallet", "--keyring-backend", "test"],
        ])
        self.assertNotIn("Wallet is ready.", result.stdout)

    def test_normal_and_macbook_wrappers_forward_key_and_backend(self):
        for directory in ("normal", "macbook"):
            with self.subTest(directory=directory):
                script = ROOT / "setup" / directory / "05-create-test-wallet.sh"
                result = self.run_helper("wrapper-wallet", script=script, KEY_NAME="ignored", KEYRING_BACKEND="file")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_wallet_calls(key_name="wrapper-wallet", backend="file")
                self.assert_usable_shell_exports(result.stdout, key_name="wrapper-wallet", backend="file")

    def test_missing_cli_fails_without_creating_or_querying_keys(self):
        self.cli.unlink()
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("injectived", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertNotIn("Wallet is ready.", result.stdout)

    def test_document_new_wallet_uses_step_one_settings_and_defaults_to_self(self):
        result = self.run_document_wallet_block()
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[lines.index("__WALLET_DOC_STATE__") + 1:], [
            "testwallet", "test", "inj1mockwalletaddress", "inj1mockwalletaddress", "inj1mockwalletaddress",
        ])
        self.assertEqual(self.calls(), [
            ["keys", "add", "testwallet", "--keyring-backend", "test"],
            ["keys", "show", "testwallet", "-a", "--keyring-backend", "test"],
            ["keys", "list", "--keyring-backend", "test"],
        ])

    def test_document_custom_sender_defaults_to_self(self):
        result = self.run_document_wallet_block(
            KEY_NAME="custom-sender", KEYRING_BACKEND="file",
            MOCK_ADDRESS_MAP=json.dumps({"custom-sender": "inj1mockcustomsender"}),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[lines.index("__WALLET_DOC_STATE__") + 1:], [
            "custom-sender", "file",
            "inj1mockcustomsender", "inj1mockcustomsender", "inj1mockcustomsender",
        ])
        self.assertEqual(self.calls(), [
            ["keys", "add", "custom-sender", "--keyring-backend", "file"],
            ["keys", "show", "custom-sender", "-a", "--keyring-backend", "file"],
            ["keys", "list", "--keyring-backend", "file"],
        ])

    def test_document_existing_wallet_omits_keys_add(self):
        result = self.run_document_wallet_block(existing_wallet=True, MOCK_KEY_EXISTS="yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[lines.index("__WALLET_DOC_STATE__") + 1:], [
            "testwallet", "test", "inj1mockwalletaddress", "inj1mockwalletaddress", "inj1mockwalletaddress",
        ])
        self.assertEqual(self.calls(), [
            ["keys", "show", "testwallet", "-a", "--keyring-backend", "test"],
            ["keys", "list", "--keyring-backend", "test"],
        ])


if __name__ == "__main__":
    unittest.main()
