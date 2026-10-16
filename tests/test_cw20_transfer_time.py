"""Check print-only CW20 timing with an isolated CLI; never access real wallets."""

import ast
import base64
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "Day1/1-8_cw20-transfer-time.py"
SPEC = importlib.util.spec_from_file_location("cw20_transfer_time", SCRIPT)
MEASUREMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEASUREMENT)
HASH = "AB" * 32


class Cw20TransferTimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sus-bc2-cw20-time-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.binary_directory = self.directory / "bin"
        self.workspace = self.directory / "work"
        self.home = self.directory / "home"
        for directory in (self.binary_directory, self.workspace, self.home):
            directory.mkdir()
        self.calls_file = self.directory / "calls.jsonl"
        self.response_file = self.directory / "response.json"
        # No host PATH fallback, and the mock's interpreter is absolute.
        self.cli = self.binary_directory / "injectived"
        self.cli.write_text(f"#!{sys.executable}\n" + '''
import base64
import json
import os
from pathlib import Path
import sys

arguments = sys.argv[1:]
with open(os.environ["MOCK_CALLS"], "a") as stream:
    stream.write(json.dumps(arguments) + "\\n")
if arguments[:3] != ["tx", "wasm", "execute"]:
    print("Unexpected mock CLI command", file=sys.stderr)
    sys.exit(99)
response = json.loads(Path(os.environ["MOCK_RESPONSE"]).read_text())
sys.stdout.buffer.write(base64.b64decode(response["stdout"]))
sys.stderr.buffer.write(base64.b64decode(response["stderr"]))
sys.exit(response["exit_code"])
''')
        self.cli.chmod(0o755)
        self.environment = {
            "PATH": str(self.binary_directory), "HOME": str(self.home),
            "PYTHONDONTWRITEBYTECODE": "1",
            "MOCK_CALLS": str(self.calls_file), "MOCK_RESPONSE": str(self.response_file),
            "RECIPIENT_ADDR": "inj1mockrecipient", "CONTRACT_ADDR": "inj1mockcontract",
            "CONFIRM_TX": "yes",
        }
        self.write_response()

    def write_response(self, stdout=None, stderr=b"", exit_code=0):
        if stdout is None:
            stdout = json.dumps({"txhash": HASH.lower(), "code": 0}).encode() + b"\n"
        self.response_file.write_text(json.dumps({
            "stdout": base64.b64encode(stdout).decode(),
            "stderr": base64.b64encode(stderr).decode(), "exit_code": exit_code,
        }))

    def calls(self):
        if not self.calls_file.exists():
            return []
        return [json.loads(line) for line in self.calls_file.read_text().splitlines()]

    def configured_script(self, settings=None):
        values = {"RECIPIENT_ADDR": "inj1mockrecipient", "CONTRACT_ADDR": "inj1mockcontract", "CONFIRM_TX": True}
        values.update(settings or {})
        source = SCRIPT.read_text()
        assignments = {
            target.id: node
            for node in ast.parse(source).body if isinstance(node, ast.Assign)
            for target in node.targets if isinstance(target, ast.Name)
        }
        self.assertFalse(set(values) - assignments.keys(), "Expected editable module-level settings")
        lines = source.splitlines(keepends=True)
        for name in sorted(values, key=lambda item: assignments[item].lineno, reverse=True):
            node = assignments[name]
            lines[node.lineno - 1:node.end_lineno] = [f"{name} = {values[name]!r}\n"]
        configured = self.directory / "configured-cw20-time.py"
        configured.write_text("".join(lines))
        return configured

    def run_script(self, *, settings=None, environment=None, arguments=(), original=False):
        script = SCRIPT if original else self.configured_script(settings)
        result = subprocess.run(
            [str(Path(sys.executable).resolve()), str(script), *arguments],
            cwd=self.workspace, env={**self.environment, **(environment or {})},
            capture_output=True, timeout=15,
        )
        # Fixture data is outside both directories; no exercise output is saved.
        self.assertEqual(list(self.workspace.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])
        return result

    def run_main(self, *, cli_status=0, error=None, elapsed=0.125, arguments=()):
        stdout, stderr = io.StringIO(), io.StringIO()
        events = []
        instants = iter((10.0, 10.0 + elapsed))

        def clock():
            events.append("clock")
            return next(instants)

        def run(*args, **kwargs):
            events.append("cli")
            if error is not None:
                raise error
            return subprocess.CompletedProcess(args[0], cli_status)

        with mock.patch.dict(os.environ, self.environment, clear=True), \
                mock.patch.multiple(
                    MEASUREMENT, RECIPIENT_ADDR="inj1mockrecipient", CONTRACT_ADDR="inj1mockcontract", CONFIRM_TX=True,
                ), \
                redirect_stdout(stdout), redirect_stderr(stderr), \
                mock.patch.object(MEASUREMENT.time, "perf_counter", side_effect=clock), \
                mock.patch.object(MEASUREMENT.subprocess, "run", side_effect=run) as runner:
            status = MEASUREMENT.main(list(arguments))
        return SimpleNamespace(
            returncode=status, stdout=stdout.getvalue(), stderr=stderr.getvalue(),
            runner=runner, events=events,
        )

    def assert_response_time(self, output):
        self.assertRegex(output, rb"\nResponse time: [0-9]+\.[0-9]{6} seconds\n$")

    def assert_transfer_message(self, arguments, recipient, amount):
        self.assertEqual(arguments[:3], ["tx", "wasm", "execute"])
        message = json.loads(arguments[4])
        self.assertEqual(message, {"transfer": {"recipient": recipient, "amount": amount}})
        self.assertIsInstance(message["transfer"]["amount"], str)
        self.assertFalse(any(argument == "--amount" or argument.startswith("--amount=") for argument in arguments))

    def test_defaults_execute_one_transfer_without_native_funds_or_queries(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments, = self.calls()
        self.assertEqual(arguments[3], "inj1mockcontract")
        self.assert_transfer_message(arguments, "inj1mockrecipient", "1000000")
        self.assertEqual(arguments[5:], [
            "--from=testwallet", "--keyring-backend=test", "--chain-id=injective-888",
            "--node=https://injective-testnet-rpc.publicnode.com:443",
            "--gas-prices=500000000inj", "--gas=300000",
            "--broadcast-mode", "sync", "--output", "json", "-y",
        ])
        self.assertIn(HASH.lower().encode(), result.stdout)
        self.assert_response_time(result.stdout)

    def test_custom_settings_and_json_escaping_preserve_the_recipient_and_amount(self):
        settings = {
            "KEY_NAME": "research wallet", "KEYRING_BACKEND": "file", "CHAIN_ID": "mock-chain",
            "NODE": "https://rpc.example.invalid:443", "GAS_PRICES": "700000000inj",
            "GAS": 345678, "CW20_SEND_AMOUNT": 2500000,
            "CONTRACT_ADDR": "inj1anothercontract", "RECIPIENT_ADDR": 'inj1quote"back\\slash',
        }
        result = self.run_script(settings=settings)
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments, = self.calls()
        self.assertEqual(arguments[3], settings["CONTRACT_ADDR"])
        self.assert_transfer_message(arguments, settings["RECIPIENT_ADDR"], str(settings["CW20_SEND_AMOUNT"]))
        for flag, variable in (
            ("from", "KEY_NAME"), ("keyring-backend", "KEYRING_BACKEND"), ("chain-id", "CHAIN_ID"),
            ("node", "NODE"), ("gas-prices", "GAS_PRICES"), ("gas", "GAS"),
        ):
            self.assertIn(f"--{flag}={settings[variable]}", arguments)

    def test_environment_does_not_override_cw20_source_settings_or_confirmation(self):
        result = self.run_script(environment={
            "DENOM": "factory/inj1creator/TOKEN", "SEND_AMOUNT": "987654321",
            "AMOUNT": "9000000000000000000inj", "BANK_SEND_GAS": "987654", "CONFIRM_SEND": "yes",
            "KEY_NAME": "environment wallet", "KEYRING_BACKEND": "file", "CHAIN_ID": "environment-chain",
            "NODE": "https://environment.example.invalid:443", "GAS_PRICES": "999inj", "GAS": "999999",
            "CW20_SEND_AMOUNT": "999999999", "CONTRACT_ADDR": "inj1environmentcontract",
            "RECIPIENT_ADDR": "inj1environmentrecipient", "CONFIRM_TX": "no",
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments, = self.calls()
        self.assertEqual(arguments[3], "inj1mockcontract")
        self.assert_transfer_message(arguments, "inj1mockrecipient", "1000000")
        for flag in (
            "--from=testwallet", "--keyring-backend=test", "--chain-id=injective-888",
            "--node=https://injective-testnet-rpc.publicnode.com:443",
            "--gas-prices=500000000inj", "--gas=300000",
        ):
            self.assertIn(flag, arguments)

        self.calls_file.unlink()
        blocked = self.run_script(
            settings={"CONFIRM_TX": False}, environment={"CONFIRM_TX": "yes", "CONFIRM_SEND": "yes"},
        )
        self.assertEqual(blocked.returncode, 1)
        self.assertIn(b"CONFIRM_TX", blocked.stderr)
        self.assertEqual(self.calls(), [])
        self.assertNotIn(b"Response time:", blocked.stdout)

    def test_unedited_source_cannot_send_using_exported_environment_settings(self):
        self.assertIs(MEASUREMENT.CONFIRM_TX, False)
        self.assertEqual(MEASUREMENT.RECIPIENT_ADDR, "")
        self.assertEqual(MEASUREMENT.CONTRACT_ADDR, "")
        result = self.run_script(original=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])
        self.assertNotIn(b"Response time:", result.stdout)

    def test_invalid_settings_and_options_never_call_the_cli(self):
        cases = [
            ({"RECIPIENT_ADDR": ""}, ()), ({"RECIPIENT_ADDR": "inj1 has space"}, ()),
            ({"CONTRACT_ADDR": ""}, ()), ({"CONTRACT_ADDR": "othercontract"}, ()),
            ({"CONTRACT_ADDR": "inj1 has space"}, ()),
            ({"CW20_SEND_AMOUNT": "0"}, ()), ({"CW20_SEND_AMOUNT": "1.5"}, ()),
            ({"CW20_SEND_AMOUNT": "1000000inj"}, ()), ({"GAS": "0"}, ()), ({"GAS": "invalid"}, ()),
            ({}, ("--timeout", "0")), ({}, ("--timeout", "nan")), ({}, ("--timeout", "inf")),
            ({}, ("--output", "unused.csv")),
        ]
        for settings, arguments in cases:
            with self.subTest(settings=settings, arguments=arguments):
                result = self.run_script(settings=settings, arguments=arguments)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(self.calls(), [])
                self.assertNotIn(b"Response time:", result.stdout)

    def test_response_bytes_are_printed_without_parsing_or_success_judgment(self):
        responses = (
            json.dumps({"txhash": HASH, "code": 7}, indent=2).encode() + b"\n",
            b"", b"txhash: example\ncode: 0\n", b"\xffraw\x00response",
        )
        for raw in responses:
            with self.subTest(raw=raw):
                if self.calls_file.exists():
                    self.calls_file.unlink()
                self.write_response(stdout=raw, stderr="mock diagnostic: 応答\n".encode())
                result = self.run_script()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(len(self.calls()), 1)
                self.assertTrue(result.stdout.startswith(raw))
                self.assertEqual(result.stderr, "mock diagnostic: 応答\n".encode())
                self.assertNotIn(b"accepted", result.stdout.lower())
                self.assertNotIn(b"Status:", result.stdout)
                self.assert_response_time(result.stdout)

    def test_nonzero_cli_exit_and_raw_response_are_preserved(self):
        raw = b"mock rejected transaction\n"
        self.write_response(stdout=raw, stderr=b"mock failure\n", exit_code=42)
        result = self.run_script()
        self.assertEqual(result.returncode, 42)
        self.assertEqual(len(self.calls()), 1)
        self.assertTrue(result.stdout.startswith(raw))
        self.assertEqual(result.stderr, b"mock failure\n")
        self.assert_response_time(result.stdout)

    def test_missing_cli_never_falls_back_to_the_host(self):
        self.cli.unlink()
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), [])
        self.assertIn(b"Could not run injectived:", result.stderr)
        self.assert_response_time(result.stdout)

    def test_help_does_not_need_wallet_settings_or_send(self):
        result = self.run_script(
            original=True, arguments=("--help",),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"--timeout", result.stdout)
        self.assertNotIn(b"--output", result.stdout)
        self.assertEqual(self.calls(), [])

    def test_timer_surrounds_one_uncaptured_execute(self):
        result = self.run_main(cli_status=17, elapsed=0.123456789)
        self.assertEqual(result.returncode, 17)
        self.assertEqual(result.events, ["clock", "cli", "clock"])
        self.assertEqual(result.runner.call_count, 1)
        self.assertEqual(result.runner.call_args.kwargs, {
            "stdin": subprocess.DEVNULL, "timeout": 60, "check": False,
        })
        self.assert_transfer_message(result.runner.call_args.args[0][1:], "inj1mockrecipient", "1000000")
        self.assertIn("Response time: 0.123457 seconds", result.stdout)
        self.assertEqual(self.calls(), [])

    def test_timeout_interrupt_and_os_error_print_time_without_retry(self):
        cases = (
            (subprocess.TimeoutExpired(["injectived"], 2.5), 1, "Timed out."),
            (KeyboardInterrupt(), 130, "Interrupted."),
            (OSError("mock executable unavailable"), 1, "Could not run injectived:"),
        )
        for error, status, notice in cases:
            with self.subTest(error=type(error).__name__):
                result = self.run_main(error=error, elapsed=2.5, arguments=("--timeout", "2.5"))
                self.assertEqual(result.returncode, status)
                self.assertEqual(result.events, ["clock", "cli", "clock"])
                self.assertEqual(result.runner.call_count, 1)
                self.assertEqual(result.runner.call_args.kwargs["timeout"], 2.5)
                self.assertIn(notice, result.stderr)
                if not isinstance(error, OSError):
                    self.assertIn("before another transfer", result.stderr)
                self.assertIn("Response time: 2.500000 seconds", result.stdout)


if __name__ == "__main__":
    unittest.main()
