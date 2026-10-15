"""Check setup dependency selection without installing packages or building projects."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "setup" / "normal"
BASE_PACKAGES = (
    "python3-pip python3-venv openjdk-11-jdk unzip npm jq git curl nodejs "
    "bash ca-certificates openssh-client wget"
)
APT_COMMANDS = [
    "apt-get --error-on=any -o Acquire::Retries=5 update",
    "apt-get -o Acquire::Retries=5 --with-new-pkgs upgrade -y",
    f"apt-get -o Acquire::Retries=5 --download-only install -y {BASE_PACKAGES} docker.io",
    f"apt-get -o Acquire::Retries=5 install -y {BASE_PACKAGES} docker.io",
]
APT_STAGES = (
    "Updating APT package indexes",
    "Upgrading installed packages",
    "Downloading development dependencies",
    "Installing development dependencies",
)
VERSION_COMMANDS = (
    "python3 --version", "git --version", "java -version",
    "node --version", "npm --version", "jq --version",
)


class KaliDependencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        self.log = self.directory / "commands.log"
        # No host PATH fallback: removing a mock must never expose real APT or sudo.
        for command in ("bash", "dirname", "mkdir", "sort", "chmod", "tee", "mktemp", "rm"):
            executable = shutil.which(command)
            if executable is None:
                self.fail(f"Required test utility is unavailable: {command}")
            (self.bin / command).symlink_to(executable)
        self.env = {
            "PATH": str(self.bin),
            "HOME": str(self.directory),
            "TMPDIR": str(self.directory),
            "COMMAND_LOG": str(self.log),
            "NODE_STUB_VERSION": "v24.21.0",
            "WORKDIR": str(self.directory),
            "RUN_SIMBLOCK": "no",
            "RUN_VISUALIZER": "no",
            "RESET_NODE_MODULES": "no",
            "JAVA_HOME": "",
        }
        self.apt_state = self.directory / "apt-state"
        self.apt_state.mkdir()
        self.env["APT_MOCK_STATE"] = str(self.apt_state)
        self.executable(self.bin / "sudo", 'printf "sudo %s\\n" "$*" >> "$COMMAND_LOG"\nexec "$@"')
        self.executable(self.bin / "id", 'printf "id %s\\n" "$*" >> "$COMMAND_LOG"\nprintf "%s\\n" "${ID_STUB_UID:-0}"')
        self.executable(self.bin / "apt-get", '''
printf 'apt-get %s\\n' "$*" >> "$COMMAND_LOG"
stage=""
for argument in "$@"; do
  case "$argument" in update|upgrade|install) stage="$argument" ;; esac
done
if [ "$stage" = "install" ] && [[ " $* " == *' --download-only '* ]]; then
  stage="download"
fi
state_file="$APT_MOCK_STATE/$stage.count"
attempt=0
if [ -f "$state_file" ]; then read -r attempt < "$state_file"; fi
attempt=$((attempt + 1))
printf '%s\\n' "$attempt" > "$state_file"
printf 'mock apt-get %s\\n' "$stage"
failures="${APT_FAIL_ATTEMPTS:--1}"
if [ "$stage" = "${APT_FAIL_STAGE:-}" ] && { [ "$failures" -lt 0 ] || [ "$attempt" -le "$failures" ]; }; then
  if [ "$attempt" -gt 1 ] && [ -n "${APT_LATER_FAIL_OUTPUT:-}" ]; then
    printf '%s\\n' "$APT_LATER_FAIL_OUTPUT" >&2
  elif [ -n "${APT_FAIL_OUTPUT:-}" ]; then
    printf '%s\\n' "$APT_FAIL_OUTPUT" >&2
  else
    printf 'mock apt-get failure: %s\\n' "$stage" >&2
  fi
  status="${APT_FAIL_STATUS:-100}"
  if [ "$attempt" -gt 1 ] && [ -n "${APT_LATER_FAIL_STATUS:-}" ]; then
    status="$APT_LATER_FAIL_STATUS"
  fi
  exit "$status"
fi
''')
        self.executable(self.bin / "sleep", 'printf "sleep %s\\n" "$*" >> "$COMMAND_LOG"')
        for command in (
            "apt", "git", "python3", "java", "npm", "jq", "wget", "unzip",
            "docker", "systemctl", "service", "cp", "sed", "sshd",
            "ldconfig", "mv", "usermod",
        ):
            self.executable(
                self.bin / command,
                f'''printf "%s\\n" "{command} $*" >> "$COMMAND_LOG"
if [ "${{VERSION_FAIL_COMMAND:-}}" = "{command} $*" ]; then
  exit 17
fi
case "$*" in
  --version|-version) printf '%s\\n' '{command} stub version' ;;
esac''',
            )
        self.executable(self.bin / "grep", 'printf "grep %s\\n" "$*" >> "$COMMAND_LOG"\nexit 0')
        self.executable(self.bin / "date", 'printf "%s\\n" "20261014000000"')
        self.executable(self.bin / "whoami", 'printf "%s\\n" "testuser"')
        self.executable(self.bin / "cat", '''
while IFS= read -r line; do printf '%s\\n' "$line"; done
''')
        self.executable(self.bin / "node", '''
printf 'node %s\\n' "$*" >> "$COMMAND_LOG"
if [ "${VERSION_FAIL_COMMAND:-}" = "node $*" ]; then
  exit 17
fi
printf "%s\\n" "$NODE_STUB_VERSION"
''')
        self.executable(self.bin / "find", 'printf "%s\\n" "$JDK_CANDIDATE"')
        self.app = self.directory / "visualizer"
        self.app.mkdir()
        self.env["APP_DIR"] = str(self.app)
        self.simblock = self.directory / "simblock"
        (self.simblock / ".git").mkdir(parents=True)
        self.env["SIMBLOCK_DIR"] = str(self.simblock)
        self.executable(
            self.simblock / "gradlew",
            'printf "%s\\n" "gradlew $*: $JAVA_HOME" >> "$COMMAND_LOG"',
        )
        self.java11 = self.jdk("java11", "11.0.31")
        self.env["JDK_CANDIDATE"] = str(self.java11)

    def executable(self, path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            path.unlink()
        path.write_text(f"#!/usr/bin/env bash\n{body}\n")
        path.chmod(0o755)

    def jdk(self, name, version):
        directory = self.directory / name
        self.executable(directory / "bin" / "java", f'echo \'openjdk version "{version}"\' >&2')
        self.executable(directory / "bin" / "javac", "exit 0")
        return directory

    def run_setup(self, filename, macbook=False):
        if self.log.exists():
            self.log.unlink()
        for path in self.apt_state.iterdir():
            path.unlink()
        return subprocess.run(
            [str(self.bin / "bash"), str((ROOT / "setup/macbook" if macbook else SETUP) / filename)],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=15,
        )

    def commands(self):
        return self.log.read_text() if self.log.exists() else ""

    def apt_commands(self):
        return [line for line in self.commands().splitlines() if line.startswith("apt-get ")]

    def assert_no_apt(self):
        self.assertNotRegex(self.commands(), r"(?m)^(?:sudo )?apt(?:-get)? ")

    def http_fetch_error(self, code=500):
        return (
            f"E: Failed to fetch http://mirror.example.invalid/package.deb  {code} HTTP error [IP: 192.0.2.1 80]\n"
            "E: Unable to fetch some archives, maybe run apt-get update or try with --fix-missing?"
        )

    def sleep_calls(self):
        return [line for line in self.commands().splitlines() if line.startswith("sleep ")]

    def assert_no_fetch_log_left(self):
        expected = {"bin", "apt-state", "commands.log", "visualizer", "simblock", "java11"}
        self.assertEqual({path.name for path in self.directory.iterdir()}, expected)

    def test_transient_supported_http_errors_retry_only_download_then_apply_once(self):
        for code in (500, 502, 503, 504):
            with self.subTest(code=code):
                self.env.update(APT_FAIL_STAGE="download", APT_FAIL_ATTEMPTS="1", APT_FAIL_OUTPUT=self.http_fetch_error(code))
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.apt_commands(), APT_COMMANDS[:2] + [APT_COMMANDS[2]] * 2 + APT_COMMANDS[3:])
                self.assertEqual(self.sleep_calls(), ["sleep 10"])
                self.assertIn("(attempt 2/3)", result.stdout)
                self.assertIn(str(code), result.stdout)
                self.assertIn("Installed basic packages.", result.stdout)
                self.assert_no_fetch_log_left()

    def test_multiple_supported_fetch_errors_are_retryable(self):
        self.env.update(
            APT_FAIL_STAGE="download", APT_FAIL_ATTEMPTS="1",
            APT_FAIL_OUTPUT=self.http_fetch_error(500) + "\nE: Failed to fetch http://mirror.example.invalid/second.deb  503 Service Unavailable",
        )
        result = self.run_setup("00-install-kali-packages.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.apt_commands(), APT_COMMANDS[:2] + [APT_COMMANDS[2]] * 2 + APT_COMMANDS[3:])

    def test_persistent_http_failure_stops_at_limit_before_apply(self):
        self.env.update(APT_FAIL_STAGE="download", APT_FAIL_OUTPUT=self.http_fetch_error())
        result = self.run_setup("00-install-kali-packages.sh")
        self.assertEqual(result.returncode, 100)
        self.assertEqual(self.apt_commands(), APT_COMMANDS[:2] + [APT_COMMANDS[2]] * 3)
        self.assertEqual(self.sleep_calls(), ["sleep 10", "sleep 10"])
        self.assertIn("exhausted after 3 attempts", result.stderr)
        self.assertIn(APT_STAGES[2], result.stderr)
        self.assertIn(APT_COMMANDS[2], result.stderr)
        self.assertNotIn("node --version", self.commands())
        self.assertNotIn("Installed basic packages.", result.stdout)
        self.assert_no_fetch_log_left()

    def test_permanent_or_mixed_fetch_errors_never_retry(self):
        errors = (
            self.http_fetch_error(404), self.http_fetch_error(501),
            self.http_fetch_error(500) + "\nE: Failed to fetch http://mirror.example.invalid/missing.deb  404 Not Found",
            self.http_fetch_error(500) + "\nE: The repository is not signed.",
            self.http_fetch_error(500) + "\nE: Unable to correct problems, you have held broken packages.",
            self.http_fetch_error(500) + "\nE: Sub-process /usr/bin/dpkg returned an error code (1)",
            "W: Mirror returned 500\nE: Unable to fetch some archives",
        )
        for error in errors:
            with self.subTest(error=error):
                self.env.update(APT_FAIL_STAGE="download", APT_FAIL_OUTPUT=error)
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertEqual(result.returncode, 100)
                self.assertEqual(self.apt_commands(), APT_COMMANDS[:3])
                self.assertEqual(self.sleep_calls(), [])
                self.assertNotIn("Installed basic packages.", result.stdout)

    def test_non_100_fetch_failure_never_retries_even_with_http_error(self):
        self.env.update(APT_FAIL_STAGE="download", APT_FAIL_STATUS="42", APT_FAIL_OUTPUT=self.http_fetch_error())
        result = self.run_setup("00-install-kali-packages.sh")
        self.assertEqual(result.returncode, 42)
        self.assertEqual(self.apt_commands(), APT_COMMANDS[:3])
        self.assertEqual(self.sleep_calls(), [])

    def test_later_permanent_error_uses_current_log_and_exit_status(self):
        for status in (100, 42):
            with self.subTest(status=status):
                self.env.update(
                    APT_FAIL_STAGE="download", APT_FAIL_OUTPUT=self.http_fetch_error(),
                    APT_LATER_FAIL_OUTPUT=self.http_fetch_error(404), APT_LATER_FAIL_STATUS=str(status),
                )
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertEqual(result.returncode, status)
                self.assertEqual(self.apt_commands(), APT_COMMANDS[:2] + [APT_COMMANDS[2]] * 2)
                self.assertEqual(self.sleep_calls(), ["sleep 10"])
                self.assertIn("404", result.stdout)

    def test_update_upgrade_and_apply_do_not_retry_http_errors(self):
        for stage, index in (("update", 0), ("upgrade", 1), ("install", 3)):
            with self.subTest(stage=stage):
                self.env.update(APT_FAIL_STAGE=stage, APT_FAIL_OUTPUT=self.http_fetch_error())
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertEqual(result.returncode, 100)
                self.assertEqual(self.apt_commands(), APT_COMMANDS[:index + 1])
                self.assertEqual(self.sleep_calls(), [])
                self.assertIn("500", result.stderr)
                self.assertNotIn("Installed basic packages.", result.stdout)

    def test_retry_policy_accepts_one_attempt_and_zero_delay(self):
        for attempts, failures, expected_status in ((1, -1, 100), (2, 1, 0)):
            with self.subTest(attempts=attempts):
                self.env.update(
                    APT_HTTP_MAX_ATTEMPTS=str(attempts), APT_HTTP_RETRY_DELAY="0",
                    APT_FAIL_STAGE="download", APT_FAIL_ATTEMPTS=str(failures), APT_FAIL_OUTPUT=self.http_fetch_error(),
                )
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertEqual(result.returncode, expected_status, result.stderr)
                self.assertEqual(self.sleep_calls(), ["sleep 0"] if attempts == 2 else [])
                expected = APT_COMMANDS[:2] + [APT_COMMANDS[2]] * attempts
                self.assertEqual(self.apt_commands(), expected + (APT_COMMANDS[3:] if expected_status == 0 else []))

    def test_invalid_retry_policy_stops_before_apt(self):
        for name, values in (
            ("APT_HTTP_MAX_ATTEMPTS", ("0", "-1", "bad", "1.5")),
            ("APT_HTTP_RETRY_DELAY", ("-1", "bad", "1.5")),
        ):
            for value in values:
                with self.subTest(name=name, value=value):
                    self.env[name] = value
                    try:
                        result = self.run_setup("00-install-kali-packages.sh")
                        self.assertEqual(result.returncode, 1)
                        self.assertIn(name, result.stderr)
                        self.assertEqual(self.apt_commands(), [])
                    finally:
                        self.env.pop(name)

    def test_tee_failure_cannot_turn_download_into_success(self):
        self.executable(self.bin / "tee", '''
while IFS= read -r line; do printf '%s\\n' "$line"; done
exit 74
''')
        result = self.run_setup("00-install-kali-packages.sh")
        self.assertEqual(result.returncode, 74)
        self.assertEqual(self.apt_commands(), APT_COMMANDS[:3])
        self.assertEqual(self.sleep_calls(), [])
        self.assertNotIn("node --version", self.commands())
        self.assertNotIn("Installed basic packages.", result.stdout)
        self.assert_no_fetch_log_left()

    def test_package_selection_covers_all_docker_and_ssh_options(self):
        for docker in ("yes", "no"):
            for ssh in ("yes", "no"):
                with self.subTest(docker=docker, ssh=ssh):
                    self.env.update(SETUP_DOCKER=docker, SETUP_SSH=ssh)
                    result = self.run_setup("00-install-kali-packages.sh")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    packages = BASE_PACKAGES
                    if docker == "yes":
                        packages += " docker.io"
                    if ssh == "yes":
                        packages += " openssh-server"
                    self.assertEqual(self.apt_commands(), APT_COMMANDS[:2] + [
                        f"apt-get -o Acquire::Retries=5 --download-only install -y {packages}",
                        f"apt-get -o Acquire::Retries=5 install -y {packages}",
                    ])

    def test_invalid_package_option_stops_before_any_apt(self):
        for flag in ("SETUP_DOCKER", "SETUP_SSH"):
            with self.subTest(flag=flag):
                self.env[flag] = "maybe"
                try:
                    result = self.run_setup("00-install-kali-packages.sh")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(f"{flag} must be yes or no", result.stderr)
                    self.assert_no_apt()
                    self.assertNotIn("Installed basic packages.", result.stdout)
                finally:
                    self.env.pop(flag)

    def test_basic_packages_accept_node_20_and_newer(self):
        for version in ("v20.19.0", "v24.21.0"):
            with self.subTest(version=version):
                self.env["NODE_STUB_VERSION"] = version
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.apt_commands(), APT_COMMANDS)
                self.assertEqual(result.stdout.splitlines(), [
                    f"==> {APT_STAGES[0]}", "mock apt-get update",
                    f"==> {APT_STAGES[1]}", "mock apt-get upgrade",
                    f"==> {APT_STAGES[2]} (attempt 1/3)", "mock apt-get download",
                    f"==> {APT_STAGES[3]}", "mock apt-get install",
                    "python3 stub version", "git stub version", "java stub version",
                    version, "npm stub version", "jq stub version",
                    "Installed basic packages.",
                ])
                without_sudo = [line for line in self.commands().splitlines() if not line.startswith("sudo ")]
                self.assertEqual(without_sudo, APT_COMMANDS + ["node --version"] + list(VERSION_COMMANDS))

    def test_apt_failures_keep_original_status_and_stop_pipeline(self):
        for index, stage in enumerate(("update", "upgrade", "download", "install")):
            with self.subTest(stage=stage):
                self.env["APT_FAIL_STAGE"] = stage
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertEqual(result.returncode, 100)
                self.assertEqual(self.apt_commands(), APT_COMMANDS[:index + 1])
                self.assertIn(f"==> {APT_STAGES[index]}", result.stdout)
                output = result.stdout + result.stderr if stage == "download" else result.stderr
                self.assertIn(f"mock apt-get failure: {stage}", output)
                self.assertIn(APT_STAGES[index], result.stderr)
                self.assertIn("00-install-kali-packages.sh", result.stderr)
                self.assertIn(APT_COMMANDS[index], result.stderr)
                self.assertRegex(result.stderr.lower(), r"(?:status|code)[^0-9]*100\b")
                self.assertNotIn("node --version", self.commands())
                self.assertNotIn("python3 --version", self.commands())
                self.assertNotIn("Installed basic packages.", result.stdout)

    def test_version_command_failure_never_prints_success(self):
        for command in VERSION_COMMANDS:
            with self.subTest(command=command):
                self.env["VERSION_FAIL_COMMAND"] = command
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertEqual(result.returncode, 17)
                self.assertEqual(self.apt_commands(), APT_COMMANDS)
                self.assertNotIn("Installed basic packages.", result.stdout)
                executed_versions = [
                    line for line in self.commands().splitlines() if line in VERSION_COMMANDS
                ]
                self.assertEqual(executed_versions[-1], command)

    def test_apt_diagnostic_reports_actual_line_after_source_moves(self):
        script = self.directory / "00-install-kali-packages.sh"
        source = "# Test comment to shift source lines\n" * 4 + (SETUP / script.name).read_text()
        script.write_text(source)
        self.env["APT_FAIL_STAGE"] = "update"
        result = subprocess.run(
            [str(self.bin / "bash"), str(script)], env=self.env,
            text=True, capture_output=True, timeout=15,
        )
        expected_line = next(
            number for number, line in enumerate(source.splitlines(), 1)
            if line.startswith(f'run_apt "{APT_STAGES[0]}"')
        )
        self.assertEqual(result.returncode, 100)
        self.assertIn(f"{script}:{expected_line}", result.stderr)
        self.assertEqual(self.apt_commands(), APT_COMMANDS[:1])

    def test_macbook_wrapper_preserves_apt_failure_status(self):
        self.env["APT_FAIL_STAGE"] = "upgrade"
        result = self.run_setup("00-install-kali-packages.sh", macbook=True)
        self.assertEqual(result.returncode, 100)
        self.assertEqual(self.apt_commands(), APT_COMMANDS[:2])
        self.assertIn("00-install-kali-packages.sh", result.stderr)
        self.assertIn(APT_STAGES[1], result.stderr)
        self.assertNotIn("Installed basic packages.", result.stdout)

    def test_uses_available_sudo_for_all_apt_commands(self):
        result = self.run_setup("00-install-kali-packages.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        sudo_commands = [line for line in self.commands().splitlines() if line.startswith("sudo ")]
        self.assertEqual(sudo_commands, [f"sudo {command}" for command in APT_COMMANDS])
        self.assertNotIn("id -u", self.commands())

    def test_root_without_sudo_runs_apt_directly(self):
        (self.bin / "sudo").unlink()
        self.env["ID_STUB_UID"] = "0"
        result = self.run_setup("00-install-kali-packages.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.apt_commands(), APT_COMMANDS)
        self.assertIn("id -u", self.commands())
        self.assertNotIn("sudo ", self.commands())

    def test_nonroot_without_sudo_stops_before_apt(self):
        (self.bin / "sudo").unlink()
        self.env["ID_STUB_UID"] = "1000"
        result = self.run_setup("00-install-kali-packages.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sudo command is required when not running as root", result.stderr)
        self.assertEqual(self.apt_commands(), [])
        self.assertNotIn("Installed basic packages.", result.stdout)

    def test_basic_packages_reject_old_or_unrecognizable_node(self):
        for version in ("v18.20.8", "invalid"):
            with self.subTest(version=version):
                self.env["NODE_STUB_VERSION"] = version
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Node.js 20 or later is required", result.stderr)
                self.assertNotIn("Kali rolling", result.stderr)
                self.assertNotIn("Installed basic packages.", result.stdout)
                self.assertEqual(self.apt_commands(), APT_COMMANDS)
                self.assertNotIn("python3 --version", self.commands())

    def test_visualizer_checks_node_before_npm_install(self):
        self.env["NODE_STUB_VERSION"] = "v18.20.8"
        result = self.run_setup("08-setup-proposer-visualizer.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("npm install", self.commands())

    def test_visualizer_accepts_current_node(self):
        result = self.run_setup("08-setup-proposer-visualizer.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("npm install", self.commands())

    def test_simblock_keeps_valid_java11_home(self):
        custom_java = self.jdk("custom-java11", "11.0.30")
        self.env["JAVA_HOME"] = str(custom_java)
        self.env["JDK_CANDIDATE"] = str(self.directory / "missing")
        result = self.run_setup("03-install-simblock.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"gradlew build: {custom_java}", self.commands())
        self.assert_no_apt()
        self.assertNotIn("sudo ", self.commands())

    def test_simblock_falls_back_from_java17_or_missing_home(self):
        java17 = self.jdk("java17", "17.0.16")
        for java_home in (str(java17), str(self.directory / "missing"), ""):
            with self.subTest(java_home=java_home):
                self.env["JAVA_HOME"] = java_home
                result = self.run_setup("03-install-simblock.sh")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"gradlew clean: {self.java11}", self.commands())
                self.assertIn(f"gradlew build: {self.java11}", self.commands())
                self.assert_no_apt()

    def test_simblock_rejects_java11_runtime_without_compiler(self):
        (self.java11 / "bin" / "javac").unlink()
        result = self.run_setup("03-install-simblock.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("A Java 11 JDK was not found", result.stderr)
        self.assertIn("setup/normal/00-install-kali-packages.sh", result.stderr)
        self.assertNotIn("gradlew", self.commands())
        self.assert_no_apt()

    def test_simblock_build_needs_no_sudo_or_root_privileges(self):
        (self.bin / "sudo").unlink()
        self.env["ID_STUB_UID"] = "1000"
        result = self.run_setup("03-install-simblock.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("gradlew build", self.commands())
        self.assert_no_apt()
        self.assertNotIn("id -u", self.commands())

    def test_individual_setup_missing_commands_recommend_base_installer(self):
        for filename, command in (
            ("03-install-simblock.sh", "git"),
            ("03-install-simblock.sh", "unzip"),
            ("04-install-injectived.sh", "wget"),
            ("04-install-injectived.sh", "unzip"),
            ("09-install-docker.sh", "docker"),
        ):
            with self.subTest(filename=filename, command=command):
                mock = self.bin / command
                body = mock.read_bytes()
                mock.unlink()
                try:
                    result = self.run_setup(filename)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("setup/normal/00-install-kali-packages.sh", result.stderr)
                    self.assert_no_apt()
                    self.assertNotIn("gradlew ", self.commands())
                    self.assertNotIn("wget -O", self.commands())
                    self.assertNotIn("systemctl ", self.commands())
                finally:
                    mock.write_bytes(body)
                    mock.chmod(0o755)

    def test_injectived_setup_has_no_apt_step(self):
        self.executable(self.bin / "unzip", '''
printf 'unzip %s\\n' "$*" >> "$COMMAND_LOG"
printf '#!/bin/sh\\nexit 0\\n' > injectived
''')
        self.executable(self.bin / "injectived", 'printf "injectived %s\\n" "$*" >> "$COMMAND_LOG"')
        result = self.run_setup("04-install-injectived.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("wget -O linux-amd64.zip", self.commands())
        self.assertIn("sudo mv injectived /usr/local/bin/", self.commands())
        self.assert_no_apt()

    def test_legacy_injectived_wrapper_preserves_missing_dependency_failure(self):
        (self.bin / "wget").unlink()
        result = subprocess.run(
            [str(self.bin / "bash"), str(ROOT / "scripts/injectived/install-injectived.sh")],
            env=self.env, text=True, capture_output=True, timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("wget is required", result.stderr)
        self.assertIn("setup/normal/00-install-kali-packages.sh", result.stderr)
        self.assert_no_apt()
        self.assertNotIn("unzip ", self.commands())

    def test_docker_setup_has_no_apt_step(self):
        result = self.run_setup("09-install-docker.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("systemctl start docker", self.commands())
        self.assertIn("docker --version", self.commands())
        self.assert_no_apt()

    def test_ssh_setup_has_no_apt_step_and_only_uses_mocked_config_commands(self):
        result = self.run_setup("02-setup-vscode-ssh.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("cp /etc/ssh/sshd_config", self.commands())
        self.assertIn("sed -i", self.commands())
        self.assertIn("service ssh restart", self.commands())
        self.assert_no_apt()

    def test_ssh_missing_server_recommends_opt_in_base_install(self):
        if os.access("/usr/sbin/sshd", os.X_OK):
            self.skipTest("Host /usr/sbin/sshd exists; absolute fallback cannot be hidden by PATH mocks.")
        (self.bin / "sshd").unlink()
        result = self.run_setup("02-setup-vscode-ssh.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SETUP_SSH=yes setup/normal/00-install-kali-packages.sh", result.stderr)
        self.assert_no_apt()
        self.assertNotIn("cp /etc/ssh/sshd_config", self.commands())


if __name__ == "__main__":
    unittest.main()
