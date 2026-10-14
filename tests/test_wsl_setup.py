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
            "SETUP_DOCKER", "SETUP_SSH", "TEST_AS_SUDO",
        )},
    }) + "\\n")
if os.environ.get("TEST_FAIL_STEP") == step:
    sys.exit(int(os.environ.get("TEST_FAIL_STATUS", "23")))
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
        # All installers and privileged commands must resolve to mocks, never host PATH.
        for command in ("bash", "dirname", "mkdir", "grep", "env", "ls", "chmod", "cat"):
            executable = shutil.which(command)
            if executable is None:
                self.fail(f"Required test utility is unavailable: {command}")
            (self.binary_directory / command).symlink_to(executable)
        self.log = self.directory / "commands.jsonl"
        self.environment = {
            key: value for key, value in os.environ.items()
            if not key.startswith(("SETUP_", "RUN_", "TEST_"))
            and key not in ("TARGET_REPO", "WORKDIR", "VENV_DIR", "APP_DIR", "CW_PLUS_DIR")
        }
        self.environment.update(
            PATH=str(self.binary_directory),
            TEST_LOG=str(self.log),
        )

    def write_stub(self, path, body=""):
        if path.is_symlink():
            path.unlink()
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
if sys.argv[1:] == ["--version"]:
    print("Python stub version")
    sys.exit(0)
assert sys.argv[1:3] == ["-m", "venv"], sys.argv
binary_directory = Path(sys.argv[3]) / "bin"
binary_directory.mkdir(parents=True, exist_ok=True)
python = binary_directory / "python"
python.write_text({venv_body!r})
python.chmod(0o755)
''')

    def use_real_setup_children_with_mocked_commands(self):
        for name in (
            "00-install-kali-packages.sh", "03-install-simblock.sh",
            "04-install-injectived.sh", "08-setup-proposer-visualizer.sh", "09-install-docker.sh",
        ):
            shutil.copyfile(ROOT / "setup/normal" / name, self.setup_directory / name)
        for command in ("git", "java", "npm", "jq", "wget", "mv", "docker", "service", "systemctl", "ldconfig", "injectived"):
            self.write_stub(self.binary_directory / command, 'print("mock command version")\n')
        self.write_stub(self.binary_directory / "apt", "sys.exit(99)\n")
        self.write_stub(self.binary_directory / "apt-get", '''
stage = next(argument for argument in sys.argv[1:] if argument in ("update", "upgrade", "install"))
if os.environ.get("TEST_FAIL_APT_STAGE") == stage:
    print("mock APT failure", file=sys.stderr)
    sys.exit(100)
''')
        self.write_stub(self.binary_directory / "sudo", '''
sys.exit(subprocess.run(sys.argv[1:], env={**os.environ, "TEST_AS_SUDO": "yes"}).returncode)
''')
        self.write_stub(self.binary_directory / "node", 'print("v24.21.0")\n')
        self.write_stub(self.binary_directory / "unzip", '''
Path("injectived").write_text("#!/bin/sh\\nexit 0\\n")
''')
        java_home = self.directory / "java11"
        (java_home / "bin").mkdir(parents=True)
        self.write_stub(java_home / "bin/java", 'print(\'openjdk version "11.0.31"\', file=sys.stderr)\n')
        self.write_stub(java_home / "bin/javac")
        self.environment["JAVA_HOME"] = str(java_home)
        simblock = self.directory / "simblock"
        (simblock / ".git").mkdir(parents=True)
        self.write_stub(simblock / "gradlew")

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
        self.assertEqual(by_step["00-install-kali-packages.sh"]["env"]["SETUP_DOCKER"], "yes")
        self.assertEqual(by_step["00-install-kali-packages.sh"]["env"]["SETUP_SSH"], "no")
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

    def test_package_flags_are_forwarded_to_base_installer(self):
        for docker in ("yes", "no"):
            for ssh in ("yes", "no"):
                with self.subTest(docker=docker, ssh=ssh):
                    if self.log.exists():
                        self.log.unlink()
                    result = self.run_script(
                        self.entry, SETUP_DOCKER=docker, SETUP_SSH=ssh, SETUP_CW20="no",
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    base = self.commands()[0]
                    self.assertEqual(base["step"], "00-install-kali-packages.sh")
                    self.assertEqual(base["env"]["SETUP_DOCKER"], docker)
                    self.assertEqual(base["env"]["SETUP_SSH"], ssh)

    def test_full_setup_has_one_apt_update_upgrade_and_install(self):
        self.use_real_setup_children_with_mocked_commands()
        result = self.run_script(self.entry)
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.commands()
        apt = [command for command in commands if command["step"] == "apt-get"]
        stages = [
            next(argument for argument in command["args"] if argument in ("update", "upgrade", "install"))
            for command in apt
        ]
        self.assertEqual(stages, ["update", "upgrade", "install"])
        self.assertFalse(any(command["step"] == "apt" for command in commands))
        self.assertTrue(any(command["step"] == "gradlew" and command["args"] == ["build"] for command in commands))
        self.assertTrue(any(command["step"] == "injectived" for command in commands))
        self.assertTrue(any(command["step"] == "docker" for command in commands))

    def test_base_apt_failure_stops_all_later_setup(self):
        self.use_real_setup_children_with_mocked_commands()
        result = self.run_script(self.entry, TEST_FAIL_APT_STAGE="install")
        self.assertEqual(result.returncode, 100)
        commands = self.commands()
        self.assertFalse(any(command["step"] in ("gradlew", "wget", "npm", "docker") for command in commands))
        self.assertFalse(any(command["step"] == "python3" and command["args"][:2] == ["-m", "venv"] for command in commands))
        self.assertNotIn("Installed basic packages.", result.stdout)

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
        self.source_files = {
            "Cargo.toml": '[workspace]\nmembers = ["contracts/*", "packages/*"]\n',
            "Cargo.lock": "# Existing lockfile must remain unchanged\n",
            "contracts/cw20-base/Cargo.toml": '[package]\nname = "cw20-base"\nversion = "2.0.0"\n',
            "contracts/cw20-base/src/lib.rs": "// cw20-base source\n",
            "contracts/other-contract/src/lib.rs": "// unrelated contract source\n",
            "packages/cw20/src/lib.rs": "// local dependency source\n",
        }
        for filename, contents in self.source_files.items():
            path = self.cw_plus / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
        (self.cw_plus / "artifacts").mkdir()
        (self.cw_plus / "artifacts/cw20_base.wasm").write_bytes(b"stale WASM")
        (self.cw_plus / "artifacts/other_contract.wasm").write_bytes(b"unneeded WASM")
        (self.cw_plus / "artifacts/checksums.txt").write_text("stale checksums\n")
        self.environment["CW_PLUS_DIR"] = str(self.cw_plus)
        self.environment["WORKDIR"] = str(self.directory)
        self.optimizer = self.directory / "optimizer stub"
        self.write_stub(self.optimizer, '''
assert sys.argv[1:] == ["./contracts/cw20-base"], sys.argv
if os.environ.get("TEST_OPTIMIZER_FAILURE") == "yes":
    sys.exit(37)
artifacts = Path("artifacts")
artifacts.mkdir(exist_ok=True)
mode = os.environ.get("TEST_WASM_OUTPUT", "fresh")
if mode == "fresh":
    (artifacts / "cw20_base.wasm").write_bytes(b"fresh CW20 WASM")
elif mode == "empty":
    (artifacts / "cw20_base.wasm").write_bytes(b"")
else:
    assert mode == "missing", mode
(artifacts / "checksums.txt").write_text("fresh cw20_base.wasm checksum\\n")
''')
        self.environment["TEST_OPTIMIZER_PATH"] = str(self.optimizer)
        self.write_stub(self.binary_directory / "rm", '''
assert sys.argv[1] == "-f", sys.argv
workspace = Path(os.environ["CW_PLUS_DIR"]).resolve()
assert Path.cwd().resolve() == workspace
for filename in sys.argv[2:]:
    target = Path(filename)
    assert target.parent == Path("artifacts"), target
    assert target.name.endswith(".wasm") or target.name == "checksums.txt", target
    target.unlink(missing_ok=True)
''')
        self.write_stub(self.binary_directory / "docker", '''
import shlex

if sys.argv[1:] == ["info"]:
    mode = os.environ["TEST_DOCKER_ACCESS"]
    sys.exit(0 if mode == "direct" or (mode == "sudo" and os.environ.get("TEST_AS_SUDO") == "yes") else 1)
assert sys.argv[1:3] == ["run", "--rm"], sys.argv
arguments = sys.argv[1:]
bind = arguments[arguments.index("-v") + 1]
assert bind.endswith(":/code"), bind
workspace = Path(bind[:-len(":/code")]).resolve()
assert workspace == Path(os.environ["CW_PLUS_DIR"]).resolve(), workspace
assert workspace.is_relative_to(Path(os.environ["WORKDIR"]).resolve()), workspace
assert arguments[arguments.index("--entrypoint") + 1] == "/bin/sh"
image_index = arguments.index("cosmwasm/workspace-optimizer:0.17.0")
assert arguments[image_index + 1] == "-c", arguments
script = arguments[image_index + 2]
assert script.count("/usr/local/bin/optimize.sh") == 1, script
if os.environ.get("TEST_DOCKER_RUN_FAILURE") == "yes":
    sys.exit(29)
script = script.replace("/usr/local/bin/optimize.sh", shlex.quote(os.environ["TEST_OPTIMIZER_PATH"]))
sys.exit(subprocess.run(["/bin/sh", "-c", script], cwd=workspace, env=os.environ).returncode)
''')
        self.write_stub(self.binary_directory / "sudo", '''
sys.exit(subprocess.run(sys.argv[1:], env={**os.environ, "TEST_AS_SUDO": "yes"}).returncode)
''')
        self.write_stub(self.binary_directory / "git", "sys.exit(98)\n")

    def docker_runs(self):
        return [item for item in self.commands() if item["step"] == "docker" and item["args"][0] == "run"]

    def assert_sources_unchanged(self):
        for filename, contents in self.source_files.items():
            self.assertEqual((self.cw_plus / filename).read_text(), contents, filename)

    def assert_fresh_artifacts_only(self):
        artifacts = self.cw_plus / "artifacts"
        self.assertEqual({path.name for path in artifacts.iterdir()}, {"cw20_base.wasm", "checksums.txt"})
        self.assertEqual((artifacts / "cw20_base.wasm").read_bytes(), b"fresh CW20 WASM")
        self.assertEqual((artifacts / "checksums.txt").read_text(), "fresh cw20_base.wasm checksum\n")

    def test_uses_direct_docker_access_when_available(self):
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="direct")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([item["step"] for item in self.commands() if item["step"] == "docker"], ["docker", "docker"])
        runs = self.docker_runs()
        self.assertEqual(len(runs), 1)
        self.assertIn("type=volume,source=cw20_base_cache,target=/target", runs[0]["args"])
        self.assertIn("type=volume,source=registry_cache,target=/usr/local/cargo/registry", runs[0]["args"])
        optimizer_calls = [item for item in self.commands() if item["step"] == self.optimizer.name]
        self.assertEqual([item["args"] for item in optimizer_calls], [["./contracts/cw20-base"]])
        self.assert_fresh_artifacts_only()
        self.assert_sources_unchanged()

    def test_falls_back_to_sudo_without_new_shell(self):
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="sudo")
        self.assertEqual(result.returncode, 0, result.stderr)
        runs = self.docker_runs()
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["env"]["TEST_AS_SUDO"], "yes")
        self.assert_fresh_artifacts_only()

    def test_unavailable_docker_fails_before_clone_or_build(self):
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="unavailable")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Docker Engine is unavailable", result.stderr)
        self.assertTrue(all(item["step"] != "git" for item in self.commands()))
        self.assertTrue(all(item["args"][0] != "run" for item in self.commands()))
        self.assert_sources_unchanged()
        self.assertEqual((self.cw_plus / "artifacts/cw20_base.wasm").read_bytes(), b"stale WASM")

    def test_missing_docker_recommends_base_install_and_service_start(self):
        (self.binary_directory / "docker").unlink()
        result = self.run_script(self.entry)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SETUP_DOCKER=yes", result.stderr)
        self.assertIn("setup/normal/00-install-kali-packages.sh", result.stderr)
        self.assertIn("setup/normal/09-install-docker.sh", result.stderr)
        self.assertEqual(self.commands(), [])

    def test_missing_fresh_wasm_never_reuses_stale_artifact(self):
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="direct", TEST_WASM_OUTPUT="missing")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cw20_base.wasm", result.stderr)
        self.assertFalse((self.cw_plus / "artifacts/cw20_base.wasm").exists())
        self.assertFalse((self.cw_plus / "artifacts/other_contract.wasm").exists())
        self.assert_sources_unchanged()

    def test_missing_contract_manifest_stops_before_artifact_cleanup_or_build(self):
        (self.cw_plus / "contracts/cw20-base/Cargo.toml").unlink()
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="direct")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contracts/cw20-base/Cargo.toml", result.stderr)
        self.assertEqual(self.docker_runs(), [])
        self.assertFalse(any(item["step"] in ("rm", self.optimizer.name) for item in self.commands()))
        self.assertEqual((self.cw_plus / "artifacts/cw20_base.wasm").read_bytes(), b"stale WASM")

    def test_empty_generated_wasm_is_rejected(self):
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="direct", TEST_WASM_OUTPUT="empty")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cw20_base.wasm", result.stderr)
        self.assertEqual((self.cw_plus / "artifacts/cw20_base.wasm").stat().st_size, 0)

    def test_optimizer_failure_keeps_status_and_does_not_generate_wasm(self):
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="direct", TEST_OPTIMIZER_FAILURE="yes")
        self.assertEqual(result.returncode, 37)
        self.assertFalse((self.cw_plus / "artifacts/cw20_base.wasm").exists())
        self.assert_sources_unchanged()

    def test_docker_failure_keeps_status_before_cleanup_or_optimizer(self):
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="direct", TEST_DOCKER_RUN_FAILURE="yes")
        self.assertEqual(result.returncode, 29)
        self.assertFalse(any(item["step"] == self.optimizer.name for item in self.commands()))
        self.assertEqual((self.cw_plus / "artifacts/cw20_base.wasm").read_bytes(), b"stale WASM")
        self.assert_sources_unchanged()

    def test_source_path_with_spaces_is_mounted_and_built_correctly(self):
        target = self.directory / "cw plus source"
        self.cw_plus.rename(target)
        self.cw_plus = target
        self.environment["CW_PLUS_DIR"] = str(target)
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="direct")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"{target}:/code", self.docker_runs()[0]["args"])
        self.assert_fresh_artifacts_only()
        self.assert_sources_unchanged()

    def test_fresh_clone_uses_shallow_history(self):
        shutil.rmtree(self.cw_plus)
        self.write_stub(self.binary_directory / "git", f'''
arguments = sys.argv[1:]
assert arguments[:3] == ["clone", "--depth", "1"], arguments
assert arguments[-2] == "https://github.com/CosmWasm/cw-plus.git", arguments
destination = Path(arguments[-1]).resolve()
assert destination == Path(os.environ["CW_PLUS_DIR"]).resolve()
(destination / ".git").mkdir(parents=True)
for filename, contents in {self.source_files!r}.items():
    target = destination / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(contents)
''')
        result = self.run_script(self.entry, TEST_DOCKER_ACCESS="direct")
        self.assertEqual(result.returncode, 0, result.stderr)
        clone_calls = [item for item in self.commands() if item["step"] == "git"]
        self.assertEqual(len(clone_calls), 1)
        self.assert_fresh_artifacts_only()
        self.assert_sources_unchanged()


if __name__ == "__main__":
    unittest.main()
