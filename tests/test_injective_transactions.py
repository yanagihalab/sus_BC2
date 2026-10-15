"""Check transaction confirmation with an isolated CLI mock; never submit real transactions."""

import base64
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/injectived/tx-utils.sh"
HASH = "A" * 64
OTHER_HASH = "B" * 64
ADDRESS = "inj1mocksender"
RECIPIENT = "inj1mockrecipient"
CONTRACT = "inj1mockcontract"


def confirmed(*, txhash=HASH, code=0, height="12", **fields):
    return {"txhash": txhash, "code": code, "height": height, **fields}


def event(event_type, key, value):
    return {"type": event_type, "attributes": [{"key": key, "value": value}]}


class InjectiveTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sus-bc2-tx-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.binary_directory = self.directory / "bin"
        self.binary_directory.mkdir()
        self.log = self.directory / "calls.jsonl"
        self.configuration = self.directory / "responses.json"
        self.state_file = self.directory / "mock-state.json"
        # Every executable is selected explicitly; there is no host PATH fallback.
        for command in ("bash", "cat", "dirname", "env", "grep", "jq", "tr"):
            executable = shutil.which(command)
            if executable is None:
                self.fail(f"Required test utility is unavailable: {command}")
            (self.binary_directory / command).symlink_to(executable)
        self.write_mock("injectived", '''
arguments = sys.argv[1:]
with open(os.environ["MOCK_LOG"], "a") as stream:
    stream.write(json.dumps(arguments) + "\\n")
configuration = json.loads(Path(os.environ["MOCK_CONFIG"]).read_text())
state_path = Path(os.environ["MOCK_STATE"])
state = json.loads(state_path.read_text()) if state_path.exists() else {"queries": 0, "transactions": []}

def emit(response):
    output = response.get("output", {})
    print(output if isinstance(output, str) else json.dumps(output))
    if response.get("stderr"):
        print(response["stderr"], file=sys.stderr)
    sys.exit(response.get("status", 0))

if arguments[:2] == ["keys", "show"]:
    print("inj1mocksender")
elif arguments == ["tx", "tokenfactory", "set-denom-metadata", "--help"]:
    print("Usage: injectived tx tokenfactory set-denom-metadata [description] [base] [display] [name] [symbol] [uri] [uri-hash] [denom-units] [decimals] [shouldDisableAdminBurn] [flags]")
elif arguments[:1] == ["tx"]:
    state["transactions"].append(arguments)
    state_path.write_text(json.dumps(state))
    if configuration.get("flow"):
        emit({"output": {"txhash": f"{len(state['transactions']):064X}", "code": 0, "height": "0"}})
    emit(configuration.get("broadcast", {"output": {"txhash": "A" * 64, "code": 0, "height": "0"}}))
elif arguments[:2] in (["q", "tx"], ["query", "tx"]):
    state["queries"] += 1
    state_path.write_text(json.dumps(state))
    if configuration.get("flow"):
        txhash = arguments[2]
        transaction = state["transactions"][int(txhash, 16) - 1]
        events = []
        if transaction[:3] == ["tx", "wasm", "store"]:
            events = [{"type": "store_code", "attributes": [{"key": "code_id", "value": "73"}]}]
        elif transaction[:3] == ["tx", "wasm", "instantiate"]:
            events = [{"type": "instantiate", "attributes": [{"key": "_contract_address", "value": "inj1mockcontract"}]}]
        emit({"output": {"tx_response": {"txhash": txhash, "code": 0, "height": "12", "logs": [{"events": events}]}}})
    responses = configuration.get("queries", [{"output": {"txhash": "A" * 64, "code": 0, "height": "12"}}])
    emit(responses[min(state["queries"] - 1, len(responses) - 1)])
elif configuration.get("flow") and arguments[:3] in (["query", "bank", "balances"], ["q", "bank", "balances"]):
    print(json.dumps({"balances": []}))
elif configuration.get("flow") and arguments[:4] == ["q", "wasm", "contract-state", "smart"]:
    print(json.dumps({"data": {"balance": "1000000"}}))
else:
    print("Unexpected mock CLI call", file=sys.stderr)
    sys.exit(99)
''')
        self.write_mock("sleep", '''
with open(os.environ["MOCK_LOG"], "a") as stream:
    stream.write(json.dumps(["sleep", *sys.argv[1:]]) + "\\n")
''')
        self.environment = {
            "PATH": str(self.binary_directory), "HOME": str(self.directory),
            "MOCK_LOG": str(self.log), "MOCK_CONFIG": str(self.configuration),
            "MOCK_STATE": str(self.state_file),
            "CHAIN_ID": "injective-888", "NODE": "https://rpc.example.invalid:443",
        }
        self.configure()

    def write_mock(self, name, body):
        path = self.binary_directory / name
        path.write_text(f"#!{sys.executable}\n" + "import json\nimport os\nfrom pathlib import Path\nimport sys\n" + body)
        path.chmod(0o755)

    def configure(self, *, broadcast=None, queries=None, **settings):
        configuration = dict(settings)
        if broadcast is not None:
            configuration["broadcast"] = broadcast
        if queries is not None:
            configuration["queries"] = queries
        self.configuration.write_text(json.dumps(configuration))
        for path in (self.log, self.state_file):
            if path.exists():
                path.unlink()

    def run_shell(self, body, *, cwd=None, **environment):
        capture = '''
capture_tx_state() {
  tx_test_status=$?
  printf '\\n__TX_TEST_STATE__\\n'
  jq -nc --arg hash "${TX_HASH-}" --arg result "${TX_RESULT-}" \\
    --arg event "${EVENT_VALUE-}" --arg code_id "${CODE_ID-}" --arg contract "${CONTRACT_ADDR-}" \\
    --arg create_hash "${CREATE_DENOM_TX_HASH-}" --arg metadata_hash "${METADATA_TX_HASH-}" \\
    --arg tf_mint_hash "${TOKENFACTORY_MINT_TX_HASH-}" --arg tf_send_hash "${TOKENFACTORY_SEND_TX_HASH-}" \\
    --arg store_hash "${STORE_TX_HASH-}" --arg instantiate_hash "${INSTANTIATE_TX_HASH-}" \\
    --arg send_hash "${CW20_SEND_TX_HASH-}" --arg mint_hash "${CW20_MINT_TX_HASH-}" \\
    '{hash:$hash,result:$result,event:$event,code_id:$code_id,contract:$contract,hashes:[$create_hash,$metadata_hash,$tf_mint_hash,$tf_send_hash,$store_hash,$instantiate_hash,$send_hash,$mint_hash]}'
  exit "$tx_test_status"
}
trap capture_tx_state EXIT
'''
        result = subprocess.run(
            [str(self.binary_directory / "bash"), "-u", "-c", capture + body],
            cwd=cwd or self.directory,
            env={**self.environment, **environment},
            capture_output=True, text=True, timeout=30,
        )
        self.assertIn("__TX_TEST_STATE__\n", result.stdout, result.stderr)
        state = json.loads(result.stdout.rsplit("__TX_TEST_STATE__\n", 1)[1])
        return result, state

    def run_transaction(self, **environment):
        return self.run_shell('source "$TX_HELPER"\nrun_tx injectived tx mock --output json --broadcast-mode sync -y', TX_HELPER=str(HELPER), **environment)

    def document_main_program(self, heading):
        document = (ROOT / "docs/injective-setup.md").read_text()
        document = re.sub(r"<details>.*?</details>", "", document, flags=re.DOTALL)
        section = re.search(
            rf"^{re.escape(heading)}[^\n]*\n(.*?)(?=^### |^## |\Z)",
            document, flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(section, f"Expected documented section: {heading}")
        blocks = re.findall(r"^```bash\s*\n(.*?)^```", section.group(1), flags=re.MULTILINE | re.DOTALL)
        self.assertTrue(blocks, f"Expected documented commands: {heading}")
        return "\n".join(blocks)

    def transaction_workspace(self):
        workspace = self.directory / "workspace"
        workspace.mkdir()
        (workspace / "scripts").symlink_to(ROOT / "scripts", target_is_directory=True)
        (workspace / "setup").symlink_to(ROOT / "setup", target_is_directory=True)
        wasm = self.directory / "sample.wasm"
        wasm.write_bytes(b"mock wasm")
        return workspace, wasm

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def sends(self):
        return [call for call in self.calls() if call[:1] == ["tx"] and "--help" not in call]

    def queries(self):
        return [call for call in self.calls() if call[:2] in (["q", "tx"], ["query", "tx"])]

    def sleeps(self):
        return [call for call in self.calls() if call[:1] == ["sleep"]]

    def assert_failed_without_result(self, result, state, *, sends=1):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(state["result"], "", "A failed transaction must not retain an old successful result")
        self.assertEqual(len(self.sends()), sends)

    def test_success_sends_once_and_exports_confirmed_result(self):
        result, state = self.run_transaction()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["hash"], HASH)
        response = json.loads(state["result"])
        response = response.get("tx_response", response)
        self.assertEqual(response["code"], 0)
        self.assertGreater(int(response["height"]), 0)
        self.assertEqual(len(self.sends()), 1)
        self.assertEqual(len(self.queries()), 1)
        self.assertEqual(self.sleeps(), [])

    def test_wrapped_broadcast_and_query_responses_are_supported(self):
        self.configure(
            broadcast={"output": {"tx_response": confirmed(height="0")}},
            queries=[{"output": {"tx_response": confirmed()}}],
        )
        result, state = self.run_transaction()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["hash"], HASH)
        self.assertEqual(len(self.sends()), 1)

    def test_success_exports_hash_and_result_to_child_commands(self):
        result, _ = self.run_shell(
            'source "$TX_HELPER"\n'
            'run_tx injectived tx mock || exit $?\n'
            'bash -uc \'[ "$TX_HASH" = "$EXPECTED_HASH" ] && [ -n "$TX_RESULT" ]\'',
            TX_HELPER=str(HELPER), EXPECTED_HASH=HASH,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_hash_var_is_exported_only_after_confirmation(self):
        result, state = self.run_shell(
            'source "$TX_HELPER"\n'
            'run_tx --hash-var STORE_TX_HASH injectived tx mock || exit $?\n'
            'bash -uc \'[ "$STORE_TX_HASH" = "$EXPECTED_HASH" ]\'',
            TX_HELPER=str(HELPER), EXPECTED_HASH=HASH, STORE_TX_HASH=OTHER_HASH,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["hashes"][4], HASH)
        self.assertEqual(len(self.sends()), 1)
        self.assertEqual(len(self.queries()), 1)

    def test_hash_var_is_cleared_on_broadcast_delivery_and_timeout_failure(self):
        for configuration in (
            {"broadcast": {"output": "", "status": 42}},
            {"broadcast": {"output": confirmed(code=5, height="0")}},
            {"queries": [{"output": confirmed(code=9)}]},
            {"queries": [{"output": "", "status": 1}]},
        ):
            with self.subTest(configuration=configuration):
                self.configure(**configuration)
                result, state = self.run_shell(
                    'source "$TX_HELPER"\nrun_tx --hash-var STORE_TX_HASH injectived tx mock',
                    TX_HELPER=str(HELPER), TX_MAX_ATTEMPTS="2", TX_RETRY_DELAY="0",
                    STORE_TX_HASH=OTHER_HASH, TX_HASH=OTHER_HASH, TX_RESULT="stale",
                )
                self.assert_failed_without_result(result, state)
                self.assertEqual(state["hashes"][4], "")

    def test_invalid_hash_var_names_do_not_submit_a_transaction(self):
        for name in ("TX_HASH", "store_tx_hash", "-bad", "STORE_TX_HASH;bad"):
            with self.subTest(name=name):
                self.configure()
                result, state = self.run_shell(
                    'source "$TX_HELPER"\nrun_tx --hash-var "$INVALID_NAME" injectived tx mock',
                    TX_HELPER=str(HELPER), INVALID_NAME=name, TX_RESULT="stale",
                )
                self.assert_failed_without_result(result, state, sends=0)
                self.assertEqual(self.queries(), [])

    def test_pending_query_then_confirmation_never_resubmits(self):
        self.configure(queries=[
            {"output": "", "status": 1, "stderr": "transaction not found"},
            {"output": confirmed()},
        ])
        result, state = self.run_transaction()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["hash"], HASH)
        self.assertEqual(len(self.sends()), 1)
        self.assertEqual(len(self.queries()), 2)
        self.assertEqual(self.sleeps(), [["sleep", "2"]])

    def test_nonzero_broadcast_code_stops_before_query(self):
        self.configure(broadcast={"output": confirmed(code=5, height="0", raw_log="rejected")})
        result, state = self.run_transaction(TX_RESULT=json.dumps(confirmed(txhash=OTHER_HASH)))
        self.assert_failed_without_result(result, state)
        self.assertEqual(self.queries(), [])

    def test_broadcast_cli_failure_keeps_status_and_never_queries(self):
        self.configure(broadcast={"output": confirmed(height="0"), "status": 42, "stderr": "mock broadcast failure"})
        result, state = self.run_transaction(TX_HASH=OTHER_HASH, TX_RESULT="stale")
        self.assertEqual(result.returncode, 42)
        self.assert_failed_without_result(result, state)
        self.assertEqual(state["hash"], "")
        self.assertEqual(self.queries(), [])

    def test_malformed_or_incomplete_broadcast_cannot_use_stale_state(self):
        for output in ("not json", {}, {"txhash": HASH}, {"code": 0}, {"code": 0, "txhash": ""}, {"code": 0, "txhash": "not-a-txhash"}):
            with self.subTest(output=output):
                self.configure(broadcast={"output": output})
                result, state = self.run_transaction(TX_HASH=OTHER_HASH, TX_RESULT="stale")
                self.assert_failed_without_result(result, state)
                self.assertNotEqual(state["hash"], OTHER_HASH)
                self.assertEqual(self.queries(), [])

    def test_failed_delivery_does_not_resubmit_or_retain_result(self):
        self.configure(queries=[{"output": confirmed(code=9, raw_log="out of gas")}])
        result, state = self.run_transaction(TX_RESULT="stale")
        self.assert_failed_without_result(result, state)
        self.assertEqual(len(self.queries()), 1)

    def test_invalid_confirmations_cannot_succeed(self):
        for output in (
            "not json", {"txhash": HASH, "height": "12"},
            {"txhash": HASH, "code": 0}, {"code": 0, "height": "12"}, confirmed(txhash=OTHER_HASH),
            confirmed(height="0"), confirmed(height="-1"),
        ):
            with self.subTest(output=output):
                self.configure(queries=[{"output": output}])
                result, state = self.run_transaction(TX_RESULT="stale")
                self.assert_failed_without_result(result, state)

    def test_zero_height_is_pending_until_a_later_confirmation(self):
        self.configure(queries=[{"output": confirmed(height="0")}, {"output": confirmed()}])
        result, state = self.run_transaction()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["hash"], HASH)
        self.assertEqual(len(self.sends()), 1)
        self.assertEqual(len(self.queries()), 2)
        self.assertEqual(self.sleeps(), [["sleep", "2"]])

    def test_query_timeout_uses_default_limit_without_resubmitting(self):
        self.configure(queries=[{"output": "", "status": 1, "stderr": "transaction not found"}])
        result, state = self.run_transaction(TX_RESULT="stale")
        self.assert_failed_without_result(result, state)
        self.assertEqual(len(self.queries()), 30)
        self.assertEqual(self.sleeps(), [["sleep", "2"]] * 29)
        self.assertEqual(state["hash"], HASH, "Keep the submitted hash so wait_tx can recover later")

    def test_wait_tx_recovers_without_any_broadcast(self):
        result, state = self.run_shell('source "$TX_HELPER"\nwait_tx "$RECOVERY_HASH"', TX_HELPER=str(HELPER), RECOVERY_HASH=HASH, TX_RESULT="stale")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["hash"], HASH)
        self.assertTrue(state["result"])
        self.assertEqual(self.sends(), [])
        self.assertEqual(len(self.queries()), 1)

    def test_wait_failure_clears_old_result_without_broadcast(self):
        self.configure(queries=[{"output": confirmed(code=5)}])
        result, state = self.run_shell('source "$TX_HELPER"\nwait_tx "$RECOVERY_HASH"', TX_HELPER=str(HELPER), RECOVERY_HASH=HASH, TX_RESULT="stale")
        self.assert_failed_without_result(result, state, sends=0)

    def test_custom_query_limit_and_delay_preserve_last_cli_failure(self):
        self.configure(queries=[{"output": "", "status": 17, "stderr": "mock RPC unavailable"}])
        result, state = self.run_transaction(TX_MAX_ATTEMPTS="2", TX_RETRY_DELAY="0", TX_RESULT="stale")
        self.assertEqual(result.returncode, 17)
        self.assert_failed_without_result(result, state)
        self.assertEqual(len(self.queries()), 2)
        self.assertEqual(self.sleeps(), [["sleep", "0"]])

    def test_invalid_poll_settings_stop_wait_before_query(self):
        for name, values in (("TX_MAX_ATTEMPTS", ("0", "-1", "bad")), ("TX_RETRY_DELAY", ("-1", "bad"))):
            for value in values:
                with self.subTest(name=name, value=value):
                    self.configure()
                    result, state = self.run_shell(
                        'source "$TX_HELPER"\nwait_tx "$RECOVERY_HASH"',
                        TX_HELPER=str(HELPER), RECOVERY_HASH=HASH, TX_RESULT="stale", **{name: value},
                    )
                    self.assert_failed_without_result(result, state, sends=0)
                    self.assertEqual(self.queries(), [])

    def event_value(self, result_json, keys="code_id", event_type="store_code"):
        return self.run_shell(
            'source "$TX_HELPER"\nEVENT_VALUE="$(tx_event_value "$EVENT_TYPE" $EVENT_KEYS)"',
            TX_HELPER=str(HELPER), TX_RESULT=json.dumps(result_json),
            EVENT_KEYS=keys, EVENT_TYPE=event_type,
        )

    def test_event_values_from_root_logs_and_wrappers(self):
        matching = event("store_code", "code_id", "73")
        for fields in (
            {"events": [matching]}, {"logs": [{"events": [matching]}]},
            {"events": [matching], "logs": [{"events": [matching]}]},
        ):
            for wrapped in (False, True):
                with self.subTest(fields=fields, wrapped=wrapped):
                    response = confirmed(**fields)
                    result, state = self.event_value({"tx_response": response} if wrapped else response)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(state["event"], "73")

    def test_event_aliases_allow_equal_values(self):
        response = confirmed(events=[
            event("instantiate", "_contract_address", CONTRACT),
            event("instantiate", "contract_address", CONTRACT),
        ])
        result, state = self.event_value(response, "_contract_address contract_address", "instantiate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["event"], CONTRACT)

    def test_json_quoted_event_values_are_unwrapped(self):
        response = confirmed(events=[event("store_code", "code_id", json.dumps("73"))])
        result, state = self.event_value(response)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["event"], "73")

    def test_base64_attribute_pairs_are_decoded_and_deduplicated(self):
        encoded_key = base64.b64encode(b"code_id").decode()
        encoded_value = base64.b64encode(b"73").decode()
        for include_plain in (False, True):
            with self.subTest(include_plain=include_plain):
                response = confirmed(
                    events=[event("store_code", "code_id", "73")] if include_plain else [],
                    logs=[{"events": [event("store_code", encoded_key, encoded_value)]}],
                )
                result, state = self.event_value(response)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(state["event"], "73")

    def test_plain_attribute_value_is_not_misread_as_base64(self):
        response = confirmed(events=[event("store_code", "code_id", "NzM=")])
        result, state = self.event_value(response)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["event"], "NzM=")

    def test_missing_or_conflicting_event_values_fail(self):
        for response in (
            confirmed(events=[]),
            confirmed(events=[event("unrelated", "code_id", "73")]),
            confirmed(events=[event("store_code", "code_id", "73"), event("store_code", "code_id", "74")]),
            confirmed(events=[event("store_code", "other", "73")]),
        ):
            with self.subTest(response=response):
                result, state = self.event_value(response)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(state["event"], "")

    def test_conflicting_event_aliases_fail(self):
        response = confirmed(events=[
            event("instantiate", "_contract_address", CONTRACT),
            event("instantiate", "contract_address", "inj1othercontract"),
        ])
        result, state = self.event_value(response, "_contract_address contract_address", "instantiate")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(state["event"], "")

    def test_confirmation_gates_prevent_cli_calls(self):
        wasm = self.directory / "sample.wasm"
        wasm.write_bytes(b"mock wasm")
        for relative, arguments in (
            ("setup/normal/07-tokenfactory-mtk.sh", ["create-denom"]),
            ("setup/normal/07-tokenfactory-mtk.sh", ["set-metadata"]),
            ("setup/normal/07-tokenfactory-mtk.sh", ["mint"]),
            ("setup/normal/07-tokenfactory-mtk.sh", ["send"]),
            ("setup/normal/11-store-cw20-code.sh", []),
        ):
            with self.subTest(script=relative, arguments=arguments):
                self.configure()
                result = subprocess.run(
                    [str(self.binary_directory / "bash"), str(ROOT / relative), *arguments],
                    env={**self.environment, "WASM_PATH": str(wasm)},
                    capture_output=True, text=True, timeout=15,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("CONFIRM_TX=yes", result.stdout + result.stderr)
                self.assertEqual(self.calls(), [])

    def test_store_uses_json_sync_and_automatic_cli_confirmation(self):
        wasm = self.directory / "sample.wasm"
        wasm.write_bytes(b"mock wasm")
        result = subprocess.run(
            [str(self.binary_directory / "bash"), str(ROOT / "setup/normal/11-store-cw20-code.sh")],
            env={**self.environment, "WASM_PATH": str(wasm), "CONFIRM_TX": "yes"},
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.sends()), 1)
        self.assertEqual(self.sends()[0][-5:], ["--output", "json", "--broadcast-mode", "sync", "-y"])

    def test_documented_cw20_store_loads_transaction_functions_in_fresh_bash(self):
        workspace, wasm = self.transaction_workspace()
        self.configure(flow=True)
        program = self.document_main_program("### 7.1.") + self.document_main_program("### 7.2.")
        result, state = self.run_shell(
            program, cwd=workspace, MY_ADDR=ADDRESS, RECIPIENT_ADDR=RECIPIENT,
            WASM_PATH=str(wasm), STORE_TX_HASH=OTHER_HASH, TX_HASH=OTHER_HASH,
            TX_RESULT="stale", CODE_ID="999", CONTRACT_ADDR="inj1oldcontract",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["hashes"][4], f"{1:064X}")
        self.assertEqual(state["hash"], f"{1:064X}")
        self.assertEqual(state["code_id"], "73")
        self.assertEqual(state["contract"], "")
        self.assertEqual(len(self.sends()), 1)
        self.assertEqual(len(self.queries()), 1)

    def test_missing_run_tx_cannot_preserve_or_export_an_old_store_hash(self):
        workspace, wasm = self.transaction_workspace()
        program, inserted = re.subn(
            r"^run_tx ", "unset -f run_tx\nrun_tx ",
            self.document_main_program("### 7.1."), flags=re.MULTILINE,
        )
        self.assertEqual(inserted, 1, "Expected one store command in step 7.1")
        result, state = self.run_shell(
            program, cwd=workspace, MY_ADDR=ADDRESS, WASM_PATH=str(wasm),
            STORE_TX_HASH=OTHER_HASH, TX_HASH=OTHER_HASH, TX_RESULT="stale",
            CODE_ID="999", CONTRACT_ADDR="inj1oldcontract",
        )
        self.assertEqual(result.returncode, 127)
        self.assert_failed_without_result(result, state, sends=0)
        self.assertEqual(state["hashes"][4], "")
        self.assertEqual(state["hash"], "")
        self.assertEqual(state["code_id"], "")
        self.assertEqual(state["contract"], "")
        self.assertEqual(self.queries(), [])

    def test_store_timeout_recovers_with_wait_only_in_the_same_session(self):
        wasm = self.directory / "sample.wasm"
        wasm.write_bytes(b"mock wasm")
        self.configure(queries=[
            {"output": "", "status": 1}, {"output": "", "status": 1},
            {"output": confirmed(events=[event("store_code", "code_id", "73")])},
        ])
        result, state = self.run_shell(
            'source "$CW20_LOADER" || exit $?\n'
            'run_tx --hash-var STORE_TX_HASH env CONFIRM_TX=yes bash "$STORE_SCRIPT"\n'
            'first_status=$?\n'
            '[ "$first_status" -ne 0 ] || exit 99\n'
            '[ -z "${STORE_TX_HASH-}" ] || exit 98\n'
            'wait_tx "$TX_HASH" || exit $?\n'
            'CODE_ID="$(tx_event_value store_code code_id)" || exit $?\n'
            'export CODE_ID STORE_TX_HASH="$TX_HASH"',
            CW20_LOADER=str(ROOT / "scripts/CW20/load-env.sh"),
            STORE_SCRIPT=str(ROOT / "setup/normal/11-store-cw20-code.sh"),
            SENDER_ADDR=ADDRESS, WASM_PATH=str(wasm),
            TX_MAX_ATTEMPTS="2", TX_RETRY_DELAY="0", STORE_TX_HASH=OTHER_HASH,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["hashes"][4], HASH)
        self.assertEqual(state["code_id"], "73")
        self.assertEqual(len(self.sends()), 1)
        self.assertEqual(len(self.queries()), 3)
        self.assertEqual(self.sleeps(), [["sleep", "0"]])

    def test_documented_tokenfactory_and_cw20_main_blocks_run_in_order(self):
        document = (ROOT / "docs/injective-setup.md").read_text()
        document = re.sub(r"<details>.*?</details>", "", document, flags=re.DOTALL)
        sections = re.findall(
            r"^## [67]\.[^\n]*\n(.*?)(?=^## |\Z)",
            document, flags=re.MULTILINE | re.DOTALL,
        )
        self.assertEqual(len(sections), 2, "Expected the two transaction walkthrough sections")
        section = "\n".join(sections)
        blocks = re.findall(r"^```bash\s*\n(.*?)^```", section, flags=re.MULTILINE | re.DOTALL)
        self.assertTrue(blocks)
        program = "\n".join(blocks)
        for placeholder in ("取得したcode_id", "取得したcontract_address", "返されたTxHash"):
            self.assertNotIn(placeholder, program)
        workspace, wasm = self.transaction_workspace()
        self.configure(flow=True)
        result, state = self.run_shell(
            program, cwd=workspace, MY_ADDR=ADDRESS, ADDR=ADDRESS, RECIPIENT_ADDR=RECIPIENT,
            KEY_NAME="testwallet", KEYRING_BACKEND="test", GAS_PRICES="500000000inj", WASM_PATH=str(wasm),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["code_id"], "73")
        self.assertEqual(state["contract"], CONTRACT)
        self.assertEqual(state["hashes"], [f"{number:064X}" for number in range(1, 9)])
        self.assertEqual(len(self.sends()), 8)
        self.assertEqual(len(self.queries()), 8)
        for command in self.sends():
            self.assertEqual(command[-5:], ["--output", "json", "--broadcast-mode", "sync", "-y"])
        initial = json.loads((workspace / "instantiate_msg.json").read_text())
        self.assertEqual(initial["initial_balances"][0]["address"], ADDRESS)
        self.assertEqual(initial["mint"]["minter"], ADDRESS)
        instantiate = next(command for command in self.sends() if command[:3] == ["tx", "wasm", "instantiate"])
        self.assertEqual(instantiate[3], "73")
        bank_send = next(command for command in self.sends() if command[:3] == ["tx", "bank", "send"])
        self.assertEqual(bank_send[4], RECIPIENT)
        executes = [command for command in self.sends() if command[:3] == ["tx", "wasm", "execute"]]
        self.assertEqual([command[3] for command in executes], [CONTRACT, CONTRACT])
        self.assertEqual(json.loads(executes[0][4])["transfer"]["recipient"], RECIPIENT)
        self.assertEqual(json.loads(executes[1][4])["mint"]["recipient"], ADDRESS)


if __name__ == "__main__":
    unittest.main()
