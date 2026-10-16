"""Check print-only INJ timing with an isolated mock CLI; never send real funds."""

import base64
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "Day1/1-6_inj-transfer-time.py"
SPEC = importlib.util.spec_from_file_location("inj_transfer_time", SCRIPT)
MEASUREMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEASUREMENT)
HASH = "AB" * 32


class InjTransferTimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sus-bc2-inj-time-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.binary_directory = self.directory / "bin"
        self.binary_directory.mkdir()
        self.workspace = self.directory / "work"
        self.workspace.mkdir()
        self.home = self.directory / "home"
        self.home.mkdir()
        self.response_file = self.directory / "response.json"
        self.calls_file = self.directory / "calls.jsonl"
        # The mock is the only executable on PATH; its interpreter is absolute.
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
if arguments[:3] != ["tx", "bank", "send"]:
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
        }
        self.settings = {
            "KEY_NAME": "testwallet", "KEYRING_BACKEND": "test",
            "CHAIN_ID": "injective-888", "NODE": "https://injective-testnet-rpc.publicnode.com:443",
            "GAS_PRICES": "500000000inj", "BANK_SEND_GAS": "200000",
            "AMOUNT": "1000000000000000inj", "RECIPIENT_ADDR": "inj1mockrecipient",
            "CONFIRM_SEND": True,
        }
        self.write_response()

    def write_response(self, stdout=None, stderr=b"", exit_code=0):
        if stdout is None:
            stdout = json.dumps({"txhash": HASH.lower(), "code": 0}).encode() + b"\n"
        if isinstance(stdout, str):
            stdout = stdout.encode()
        if isinstance(stderr, str):
            stderr = stderr.encode()
        self.response_file.write_text(json.dumps({
            "stdout": base64.b64encode(stdout).decode(),
            "stderr": base64.b64encode(stderr).decode(),
            "exit_code": exit_code,
        }))

    def calls(self):
        if not self.calls_file.exists():
            return []
        return [json.loads(line) for line in self.calls_file.read_text().splitlines()]

    def configured_source(self, settings):
        source = SCRIPT.read_text()
        for name, value in {**self.settings, **(settings or {})}.items():
            source, count = re.subn(
                rf"^{name}\s*=.*$", lambda match: f"{name} = {value!r}",
                source, count=1, flags=re.MULTILINE,
            )
            self.assertEqual(count, 1, f"Expected one editable source constant: {name}")
        configured = self.directory / "configured-inj-transfer-time.py"
        configured.write_text(source)
        return configured

    def run_script(self, *, settings=None, environment=None, arguments=(), original=False):
        script = SCRIPT if original else self.configured_source(settings)
        result = subprocess.run(
            [str(Path(sys.executable).resolve()), str(script), *arguments],
            cwd=self.workspace, env={**self.environment, **(environment or {})},
            capture_output=True, timeout=15,
        )
        # Fixture files live elsewhere, so these directories must remain empty.
        self.assertEqual(list(self.workspace.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])
        return result

    def run_main(self, *, cli_status=0, error=None, elapsed=0.125, arguments=()):
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, self.environment, clear=True), \
                mock.patch.multiple(MEASUREMENT, **self.settings), \
                redirect_stdout(stdout), redirect_stderr(stderr), \
                mock.patch.object(MEASUREMENT.time, "perf_counter", side_effect=[10.0, 10.0 + elapsed]) as clock, \
                mock.patch.object(
                    MEASUREMENT.subprocess, "run", side_effect=error,
                    return_value=subprocess.CompletedProcess(["injectived"], cli_status),
                ) as runner:
            status = MEASUREMENT.main(list(arguments))
        return SimpleNamespace(
            returncode=status, stdout=stdout.getvalue(), stderr=stderr.getvalue(),
            runner=runner, clock=clock,
        )

    def assert_response_time(self, output):
        self.assertRegex(output, rb"\nResponse time: [0-9]+\.[0-9]{6} seconds\n$")

    def test_response_and_hash_are_printed_with_elapsed_time(self):
        raw_stdout = json.dumps({"txhash": HASH.lower(), "code": 0}, indent=2).encode() + b"\n"
        raw_stderr = "mock CLI diagnostic: 応答\n".encode()
        self.write_response(stdout=raw_stdout, stderr=raw_stderr)
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)
        self.assertTrue(result.stdout.startswith(raw_stdout))
        self.assertIn(HASH.lower().encode(), result.stdout)
        self.assertEqual(result.stderr, raw_stderr)
        self.assert_response_time(result.stdout)

    def test_default_flags_use_json_sync_without_queries(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments, = self.calls()
        self.assertEqual(arguments[:6], [
            "tx", "bank", "send", "testwallet", "inj1mockrecipient", "1000000000000000inj",
        ])
        for flag in (
            "--from=testwallet", "--keyring-backend=test", "--chain-id=injective-888",
            "--node=https://injective-testnet-rpc.publicnode.com:443", "--gas-prices=500000000inj", "--gas=200000",
        ):
            self.assertIn(flag, arguments)
        self.assertEqual(arguments[arguments.index("--broadcast-mode") + 1], "sync")
        self.assertEqual(arguments[arguments.index("--output") + 1], "json")
        self.assertTrue("-y" in arguments or "--yes" in arguments)

    def test_source_settings_are_passed_as_separate_arguments_and_override_environment(self):
        settings = {
            "KEY_NAME": "research wallet", "KEYRING_BACKEND": "file", "CHAIN_ID": "mock-chain",
            "NODE": "https://other.example.invalid:443", "GAS_PRICES": "700000000inj",
            "BANK_SEND_GAS": "234567", "AMOUNT": "2000000000000000inj",
            "RECIPIENT_ADDR": "inj1differentrecipient",
        }
        environment = {
            "KEY_NAME": "environment-wallet", "KEYRING_BACKEND": "test", "CHAIN_ID": "environment-chain",
            "NODE": "https://env.example.invalid:443", "GAS_PRICES": "900000000inj",
            "BANK_SEND_GAS": "999999", "AMOUNT": "9000000000000000inj",
            "RECIPIENT_ADDR": "inj1environmentrecipient", "CONFIRM_SEND": "no",
        }
        result = self.run_script(settings=settings, environment=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments, = self.calls()
        self.assertEqual(arguments[3:6], [settings["KEY_NAME"], settings["RECIPIENT_ADDR"], settings["AMOUNT"]])
        for flag, variable in (
            ("from", "KEY_NAME"), ("keyring-backend", "KEYRING_BACKEND"), ("chain-id", "CHAIN_ID"),
            ("node", "NODE"), ("gas-prices", "GAS_PRICES"), ("gas", "BANK_SEND_GAS"),
        ):
            self.assertIn(f"--{flag}={settings[variable]}", arguments)

    def test_confirmation_guard_never_calls_the_cli(self):
        result = self.run_script(settings={"CONFIRM_SEND": False}, environment={"CONFIRM_SEND": "yes"})
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"CONFIRM_SEND", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertNotIn(b"Response time:", result.stdout)

    def test_unedited_source_preserves_safe_defaults_and_ignores_environment_confirmation(self):
        expected = {**self.settings, "RECIPIENT_ADDR": "", "CONFIRM_SEND": False}
        self.assertEqual({name: getattr(MEASUREMENT, name) for name in expected}, expected)
        result = self.run_script(
            original=True, environment={"RECIPIENT_ADDR": "inj1environmentrecipient", "CONFIRM_SEND": "yes"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])
        self.assertNotIn(b"Response time:", result.stdout)

    def test_invalid_settings_and_timeout_stop_before_sending(self):
        cases = [
            ({"RECIPIENT_ADDR": ""}, ()), ({"RECIPIENT_ADDR": "inj1 contains space"}, ()),
            ({"AMOUNT": "0inj"}, ()), ({"AMOUNT": "1"}, ()),
            ({"BANK_SEND_GAS": "0"}, ()), ({"BANK_SEND_GAS": "invalid"}, ()),
            ({}, ("--timeout", "0")), ({}, ("--timeout", "nan")), ({}, ("--timeout", "inf")),
            ({}, ("--output", "unused.csv")),
        ]
        for settings, arguments in cases:
            with self.subTest(settings=settings, arguments=arguments):
                result = self.run_script(settings=settings, arguments=arguments)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(self.calls(), [])

    def test_json_transaction_code_is_shown_without_python_success_judgment(self):
        raw = json.dumps({"txhash": HASH, "code": 7}).encode() + b"\n"
        self.write_response(stdout=raw)
        result = self.run_script()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(self.calls()), 1)
        self.assertTrue(result.stdout.startswith(raw))
        self.assertNotIn(b"accepted", result.stdout.lower())
        self.assertNotIn(b"Status:", result.stdout)
        self.assert_response_time(result.stdout)

    def test_unparseable_and_invalid_utf8_responses_are_not_modified_or_resent(self):
        responses = (b"", b"txhash: example\ncode: 0\n", b"notice\n{}", b"{", b"\xffraw\x00response")
        for raw in responses:
            with self.subTest(raw=raw):
                if self.calls_file.exists():
                    self.calls_file.unlink()
                self.write_response(stdout=raw, stderr=b"raw diagnostic\n")
                result = self.run_script()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(len(self.calls()), 1)
                self.assertTrue(result.stdout.startswith(raw))
                self.assertEqual(result.stderr, b"raw diagnostic\n")
                self.assertNotIn(b"accepted", result.stdout.lower())
                self.assert_response_time(result.stdout)

    def test_nonzero_cli_status_and_raw_response_are_preserved(self):
        raw = json.dumps({"txhash": HASH.lower(), "code": 0}).encode() + b"\n"
        self.write_response(stdout=raw, stderr=b"mock command failure\n", exit_code=42)
        result = self.run_script()
        self.assertEqual(result.returncode, 42)
        self.assertEqual(len(self.calls()), 1)
        self.assertTrue(result.stdout.startswith(raw))
        self.assertEqual(result.stderr, b"mock command failure\n")
        self.assert_response_time(result.stdout)

    def test_missing_cli_cannot_fall_back_to_the_host(self):
        self.cli.unlink()
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), [])
        self.assertIn(b"Could not run injectived:", result.stderr)
        self.assert_response_time(result.stdout)

    def test_help_works_from_an_unrelated_directory_without_cli_calls(self):
        result = self.run_script(
            arguments=("--help",), settings={"CONFIRM_SEND": False, "RECIPIENT_ADDR": ""},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"--timeout", result.stdout)
        self.assertNotIn(b"--output", result.stdout)
        self.assertEqual(self.calls(), [])

    def test_timer_surrounds_one_uncaptured_cli_call(self):
        result = self.run_main(cli_status=17, elapsed=0.123456789)
        self.assertEqual(result.returncode, 17)
        self.assertEqual(result.runner.call_count, 1)
        self.assertEqual(result.clock.call_count, 2)
        command = result.runner.call_args.args[0]
        self.assertEqual(command[:4], ["injectived", "tx", "bank", "send"])
        self.assertEqual(result.runner.call_args.kwargs, {
            "stdin": subprocess.DEVNULL, "timeout": 60, "check": False,
        })
        self.assertIn("Response time: 0.123457 seconds", result.stdout)
        self.assertEqual(self.calls(), [])

    def test_timeout_prints_time_and_notice_without_retrying(self):
        result = self.run_main(
            error=subprocess.TimeoutExpired(["injectived"], 2.5), elapsed=2.5,
            arguments=("--timeout", "2.5"),
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.runner.call_count, 1)
        self.assertEqual(result.runner.call_args.kwargs["timeout"], 2.5)
        self.assertEqual(result.clock.call_count, 2)
        self.assertIn("Timed out.", result.stderr)
        self.assertIn("before another transfer", result.stderr)
        self.assertIn("Response time: 2.500000 seconds", result.stdout)

    def test_interruption_prints_time_and_notice_without_retrying(self):
        result = self.run_main(error=KeyboardInterrupt(), elapsed=0.5)
        self.assertEqual(result.returncode, 130)
        self.assertEqual(result.runner.call_count, 1)
        self.assertEqual(result.clock.call_count, 2)
        self.assertIn("Interrupted.", result.stderr)
        self.assertIn("before another transfer", result.stderr)
        self.assertIn("Response time: 0.500000 seconds", result.stdout)

    def test_command_error_prints_time_without_retrying(self):
        result = self.run_main(error=OSError("mock executable unavailable"), elapsed=0.25)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.runner.call_count, 1)
        self.assertEqual(result.clock.call_count, 2)
        self.assertIn("Could not run injectived: mock executable unavailable", result.stderr)
        self.assertIn("Response time: 0.250000 seconds", result.stdout)


if __name__ == "__main__":
    unittest.main()
