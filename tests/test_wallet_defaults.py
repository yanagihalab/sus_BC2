"""Check recipient defaults with an isolated mock CLI; never use real wallets."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOADERS = (
    (ROOT / "scripts/injectived/load-env.sh", "MY_ADDR"),
    (ROOT / "scripts/tokenfactory/load-env.sh", "CREATOR_ADDR"),
    (ROOT / "scripts/CW20/load-env.sh", "SENDER_ADDR"),
)


class WalletRecipientDefaultsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sus-bc2-recipient-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.log = self.directory / "calls.jsonl"
        self.binary_directory = self.directory / "bin"
        self.no_cli_directory = self.directory / "no-cli"
        for directory in (self.binary_directory, self.no_cli_directory):
            directory.mkdir()
            for command in ("cat", "dirname"):
                executable = shutil.which(command)
                if executable is None:
                    self.fail(f"Required test utility is unavailable: {command}")
                (directory / command).symlink_to(executable)
        # PATH never falls back to the host, including when no mock CLI exists.
        mock = self.binary_directory / "injectived"
        mock.write_text(f"#!{sys.executable}\n" + '''
import json
import os
import sys

arguments = sys.argv[1:]
with open(os.environ["MOCK_LOG"], "a") as stream:
    stream.write(json.dumps(arguments) + "\\n")
if arguments[:2] != ["keys", "show"] or "-a" not in arguments:
    print("Unexpected mock CLI call", file=sys.stderr)
    sys.exit(99)
status = int(os.environ.get("MOCK_QUERY_STATUS", "0"))
if status:
    print("mock key not found", file=sys.stderr)
    sys.exit(status)
print(os.environ["MOCK_ADDRESS"])
''')
        mock.chmod(0o755)
        self.environment = {
            "HOME": str(self.directory),
            "MOCK_LOG": str(self.log),
            "MOCK_ADDRESS": "inj1mockownaddress",
        }

    def source_loader(self, loader, address_variable, *, with_cli=True, **environment):
        if self.log.exists():
            self.log.unlink()
        result = subprocess.run(
            [
                "/bin/bash", "-u", "-c",
                'source "$1" >/dev/null || exit $?\n'
                'printf "%s\\n" "$RECIPIENT_ADDR" "${!2}" "$KEY_NAME" "$KEYRING_BACKEND"',
                "recipient-default-test", str(loader), address_variable,
            ],
            cwd=self.directory,
            env={
                **self.environment,
                "PATH": str(self.binary_directory if with_cli else self.no_cli_directory),
                **environment,
            },
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = result.stdout.splitlines()
        self.assertEqual(len(state), 4, result.stdout)
        return state

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def assert_address_query(self, key_name="testwallet", backend="test"):
        self.assertEqual(self.calls(), [
            ["keys", "show", key_name, "-a", "--keyring-backend", backend],
        ])

    def test_unset_or_empty_recipient_uses_resolved_own_address(self):
        for loader, address_variable in LOADERS:
            for environment in ({}, {"RECIPIENT_ADDR": ""}):
                with self.subTest(loader=loader.parent.name, environment=environment):
                    state = self.source_loader(loader, address_variable, **environment)
                    self.assertEqual(state, ["inj1mockownaddress", "inj1mockownaddress", "testwallet", "test"])
                    self.assert_address_query()

    def test_explicit_recipient_is_preserved(self):
        for loader, address_variable in LOADERS:
            with self.subTest(loader=loader.parent.name):
                state = self.source_loader(loader, address_variable, RECIPIENT_ADDR="inj1explicitrecipient")
                self.assertEqual(state, ["inj1explicitrecipient", "inj1mockownaddress", "testwallet", "test"])
                self.assert_address_query()

    def test_custom_key_and_backend_are_used_and_preserved(self):
        for loader, address_variable in LOADERS:
            with self.subTest(loader=loader.parent.name):
                state = self.source_loader(
                    loader, address_variable,
                    KEY_NAME="research-wallet", KEYRING_BACKEND="file",
                )
                self.assertEqual(state, ["inj1mockownaddress", "inj1mockownaddress", "research-wallet", "file"])
                self.assert_address_query("research-wallet", "file")

    def test_existing_own_address_is_used_without_a_cli_query(self):
        for loader, address_variable in LOADERS:
            with self.subTest(loader=loader.parent.name):
                environment = {
                    "MY_ADDR": "inj1othermyaddress",
                    "CREATOR_ADDR": "inj1othercreator",
                    "SENDER_ADDR": "inj1othersender",
                    address_variable: "inj1existingownaddress",
                }
                state = self.source_loader(loader, address_variable, **environment)
                self.assertEqual(state, ["inj1existingownaddress", "inj1existingownaddress", "testwallet", "test"])
                self.assertEqual(self.calls(), [])

    def test_missing_cli_leaves_unresolved_recipient_empty(self):
        for loader, address_variable in LOADERS:
            for environment in ({}, {"RECIPIENT_ADDR": ""}):
                with self.subTest(loader=loader.parent.name, environment=environment):
                    state = self.source_loader(loader, address_variable, with_cli=False, **environment)
                    self.assertEqual(state, ["", "", "testwallet", "test"])
                    self.assertEqual(self.calls(), [])

    def test_missing_key_leaves_unresolved_recipient_empty(self):
        for loader, address_variable in LOADERS:
            for environment in ({}, {"RECIPIENT_ADDR": ""}):
                with self.subTest(loader=loader.parent.name, environment=environment):
                    state = self.source_loader(
                        loader, address_variable, MOCK_QUERY_STATUS="1", **environment,
                    )
                    self.assertEqual(state, ["", "", "testwallet", "test"])
                    self.assert_address_query()

    def test_explicit_recipient_survives_unavailable_own_address(self):
        for loader, address_variable in LOADERS:
            for with_cli in (False, True):
                with self.subTest(loader=loader.parent.name, with_cli=with_cli):
                    state = self.source_loader(
                        loader, address_variable, with_cli=with_cli,
                        MOCK_QUERY_STATUS="1", RECIPIENT_ADDR="inj1explicitrecipient",
                    )
                    self.assertEqual(state, ["inj1explicitrecipient", "", "testwallet", "test"])
                    if with_cli:
                        self.assert_address_query()
                    else:
                        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
