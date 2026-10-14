"""Exercise setup orchestration with stubs; never install packages or send transactions."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STUB_HEADER = f"#!{sys.executable}\n" + '''
import json
import os
from pathlib import Path
import subprocess
import sys

step = Path(__file__).name
with open(os.environ["TEST_LOG"], "a") as stream:
    stream.write(json.dumps({
        "step": step, "args": sys.argv[1:], "cwd": os.getcwd(),
        "env": {name: os.environ.get(name) for name in (
            "TARGET_REPO", "WORKDIR", "VENV_DIR", "APP_DIR",
            "RUN_VISUALIZER", "RUN_SIMBLOCK", "RUN_HELLO_WORLD",
            "TEST_AS_SUDO",
        )},
    }) + "\\n")
if os.environ.get("TEST_FAIL_STEP") == step:
    sys.exit(23)
'''


class SetupTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sus-bc2-setup-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.repository = self.directory / "target repo"
        self.setup_directory = self.repository / "setup" / "normal"
        self.setup_directory.mkdir(parents=True)
        (self.repository / "requirements.txt").write_text("")
        app = self.repository / "Day1" / "Proposer-visualizer"
        app.mkdir(parents=True)
        (app / "package.json").write_text("{}")
        self.binary_directory = self.directory / "bin"
        self.binary_directory.mkdir()
        self.log = self.directory / "commands.jsonl"
        self.environment = {
            key: value for key, value in os.environ.items()
            if not key.startswith(("SETUP_", "RUN_", "TEST_"))
            and key not in ("TARGET_REPO", "WORKDIR", "VENV_DIR", "APP_DIR", "CW_PLUS_DIR")
        }
        self.environment.update(
            PATH=f"{self.binary_directory}{os.pathsep}{os.defpath}",
            TEST_LOG=str(self.log),
        )

    def write_stub(self, path, body=""):
        path.write_text(STUB_HEADER + body)
        path.chmod(0o755)

    def commands(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def run_script(self, path, **environment):
        return subprocess.run(
            ["/bin/bash", str(path)], cwd=self.directory,
            env={**self.environment, **environment},
            capture_output=True, text=True, timeout=15,
        )


class WslSetupTests(SetupTestCase):
    def setUp(self):
        super().setUp()
        self.entry = self.setup_directory / "wsl-kali-experiment-env.sh"
        shutil.copyfile(ROOT / "setup/normal/wsl-kali-experiment-env.sh", self.entry)
        uname = self.binary_directory / "uname"
        uname.write_text('#!/bin/sh\nprintf "%s\\n" "${TEST_ARCH:-x86_64}"\n')
        uname.chmod(0o755)
        for source in (ROOT / "setup/normal").glob("[0-9][0-9]-*.sh"):
            self.write_stub(self.setup_directory / source.name)
        venv_body = STUB_HEADER
        self.write_stub(self.binary_directory / "python3", f'''
assert sys.argv[1:3] == ["-m", "venv"], sys.argv
binary_directory = Path(sys.argv[3]) / "bin"
binary_directory.mkdir(parents=True, exist_ok=True)
python = binary_directory / "python"
python.write_text({venv_body!r})
python.chmod(0o755)
''')

    def test_default_build_order_and_no_runtime_actions(self):
        result = self.run_script(
            self.entry, RUN_VISUALIZER="yes", RUN_SIMBLOCK="yes", RUN_HELLO_WORLD="yes",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.commands()
        self.assertEqual([item["step"] for item in commands], [
            "00-install-kali-packages.sh", "python3", "python",
            "08-setup-proposer-visualizer.sh", "03-install-simblock.sh",
            "04-install-injectived.sh", "09-install-docker.sh", "10-build-cw20-sample.sh",
        ])
        by_step = {item["step"]: item for item in commands}
        for step, flag in (
            ("08-setup-proposer-visualizer.sh", "RUN_VISUALIZER"),
            ("03-install-simblock.sh", "RUN_SIMBLOCK"),
            ("09-install-docker.sh", "RUN_HELLO_WORLD"),
        ):
            self.assertEqual(by_step[step]["env"][flag], "no")
        self.assertEqual(by_step["python"]["args"], [
            "-m", "pip", "install", "-r", str(self.repository / "requirements.txt"),
        ])

    def test_optional_builds_can_be_skipped(self):
        result = self.run_script(self.entry, **{
            flag: "no" for flag in (
                "SETUP_VISUALIZER", "SETUP_SIMBLOCK", "SETUP_INJECTIVE", "SETUP_DOCKER", "SETUP_CW20",
            )
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([item["step"] for item in self.commands()], [
            "00-install-kali-packages.sh", "python3", "python",
        ])

    def test_ssh_requires_explicit_opt_in(self):
        result = self.run_script(self.entry, SETUP_SSH="yes", SETUP_CW20="no")
        self.assertEqual(result.returncode, 0, result.stderr)
        names = [item["step"] for item in self.commands()]
        self.assertIn("02-setup-vscode-ssh.sh", names)
        self.assertNotIn("10-build-cw20-sample.sh", names)

    def test_cw20_requires_docker_before_any_install(self):
        result = self.run_script(self.entry, SETUP_DOCKER="no")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SETUP_CW20=yes requires SETUP_DOCKER=yes", result.stderr)
        self.assertEqual(self.commands(), [])

    def test_invalid_flag_is_rejected_before_any_install(self):
        result = self.run_script(self.entry, SETUP_SIMBLOCK="maybe")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SETUP_SIMBLOCK must be yes or no", result.stderr)
        self.assertEqual(self.commands(), [])

    def test_arm_rejects_default_injectived_before_any_install(self):
        result = self.run_script(self.entry, TEST_ARCH="aarch64")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported on aarch64", result.stderr)
        self.assertIn("SETUP_INJECTIVE=no", result.stderr)
        self.assertEqual(self.commands(), [])

    def test_arm_can_explicitly_skip_injectived(self):
        result = self.run_script(self.entry, TEST_ARCH="aarch64", SETUP_INJECTIVE="no")
        self.assertEqual(result.returncode, 0, result.stderr)
        names = [item["step"] for item in self.commands()]
        self.assertNotIn("04-install-injectived.sh", names)
        self.assertIn("03-install-simblock.sh", names)
        self.assertIn("10-build-cw20-sample.sh", names)

    def test_child_failure_stops_subsequent_installers(self):
        result = self.run_script(self.entry, TEST_FAIL_STEP="03-install-simblock.sh")
        self.assertEqual(result.returncode, 23)
        self.assertEqual(self.commands()[-1]["step"], "03-install-simblock.sh")

    def test_default_paths_follow_target_repository(self):
        result = self.run_script(self.entry)
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in self.commands():
            self.assertEqual(command["env"]["TARGET_REPO"], str(self.repository))
            self.assertEqual(command["env"]["WORKDIR"], str(self.repository.parent))
            self.assertEqual(command["env"]["VENV_DIR"], str(self.repository / "venv"))
            self.assertEqual(command["env"]["APP_DIR"], str(self.repository / "Day1/Proposer-visualizer"))

    def test_custom_target_and_relative_paths_are_consistent(self):
        target = self.directory / "other target"
        target.mkdir()
        (target / "requirements.txt").write_text("")
        app = target / "custom app"
        app.mkdir()
        (app / "package.json").write_text("{}")
        result = self.run_script(
            self.entry, TARGET_REPO="other target", VENV_DIR="custom venv",
            APP_DIR="custom app", WORKDIR="external repositories",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in self.commands():
            self.assertEqual(command["env"]["TARGET_REPO"], str(target))
            self.assertEqual(command["env"]["VENV_DIR"], str(target / "custom venv"))
            self.assertEqual(command["env"]["APP_DIR"], str(app))
            self.assertEqual(command["env"]["WORKDIR"], str(self.directory / "external repositories"))
        self.assertEqual(self.commands()[2]["cwd"], str(target))


class Cw20DockerAccessTests(SetupTestCase):
    def setUp(self):
        super().setUp()
        self.entry = ROOT / "setup/normal/10-build-cw20-sample.sh"
        self.cw_plus = self.directory / "cw-plus"
        (self.cw_plus / ".git").mkdir(parents=True)
        (self.cw_plus / "contracts/cw20-base").mkdir(parents=True)
        (self.cw_plus / "artifacts").mkdir()
        (self.cw_plus / "artifacts/cw20_base.wasm").write_bytes(b"stub")
        self.environment["CW_PLUS_DIR"] = str(self.cw_plus)
        self.environment["WORKDIR"] = str(self.directory)
        self.write_stub(self.binary_directory / "docker", '''
if sys.argv[1:] == ["info"]:
    mode = os.environ["TEST_DOCKER_ACCESS"]
    sys.exit(0 if mode == "direct" or (mode == "sudo" and os.environ.get("TEST_AS_SUDO") == "yes") else 1)
assert sys.argv[1:3] == ["run", "--rm"], sys.argv
''')
        self.write_stub(self.binary_directory / "sudo", '''
sys.exit(subprocess.run(sys.argv[1:], env={**os.environ, "TEST_AS_SUDO": "yes"}).returncode)
''')
        self.write_stub(self.binary_directory / "git", "sys.exit(98)\n")

    def test_uses_direct_docker_access_when_available(self):
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="direct")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([item["step"] for item in self.commands()], ["docker", "docker"])
        self.assertEqual(self.commands()[-1]["args"][-1], "cosmwasm/workspace-optimizer:0.17.0")

    def test_falls_back_to_sudo_without_new_shell(self):
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="sudo")
        self.assertEqual(result.returncode, 0, result.stderr)
        runs = [item for item in self.commands() if item["step"] == "docker" and item["args"][0] == "run"]
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["env"]["TEST_AS_SUDO"], "yes")

    def test_unavailable_docker_fails_before_clone_or_build(self):
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="unavailable")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Docker Engine is unavailable", result.stderr)
        self.assertTrue(all(item["step"] != "git" for item in self.commands()))
        self.assertTrue(all(item["args"][0] != "run" for item in self.commands()))


if __name__ == "__main__":
    unittest.main()
