"""Check setup dependency selection without installing packages or building projects."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "setup" / "normal"


class KaliDependencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        self.log = self.directory / "commands.log"
        self.env = {
            **os.environ,
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "COMMAND_LOG": str(self.log),
            "NODE_STUB_VERSION": "v24.21.0",
            "WORKDIR": str(self.directory),
            "RUN_SIMBLOCK": "no",
            "RUN_VISUALIZER": "no",
            "RESET_NODE_MODULES": "no",
            "JAVA_HOME": "",
        }
        self.executable(self.bin / "sudo", 'exec "$@"')
        for command in ("apt", "git", "python3", "java", "npm", "jq"):
            self.executable(
                self.bin / command,
                f'printf "%s\\n" "{command} $*" >> "$COMMAND_LOG"',
            )
        self.executable(self.bin / "node", 'printf "%s\\n" "$NODE_STUB_VERSION"')
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
        path.write_text(f"#!/usr/bin/env bash\n{body}\n")
        path.chmod(0o755)

    def jdk(self, name, version):
        directory = self.directory / name
        self.executable(directory / "bin" / "java", f'echo \'openjdk version "{version}"\' >&2')
        self.executable(directory / "bin" / "javac", "exit 0")
        return directory

    def run_setup(self, filename):
        if self.log.exists():
            self.log.unlink()
        return subprocess.run(
            ["bash", str(SETUP / filename)],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=15,
        )

    def commands(self):
        return self.log.read_text() if self.log.exists() else ""

    def test_basic_packages_accept_node_20_and_newer(self):
        for version in ("v20.19.0", "v24.21.0"):
            with self.subTest(version=version):
                self.env["NODE_STUB_VERSION"] = version
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("openjdk-11-jdk", self.commands())
                self.assertIn("nodejs", self.commands())

    def test_basic_packages_reject_old_or_unrecognizable_node(self):
        for version in ("v18.20.8", "invalid"):
            with self.subTest(version=version):
                self.env["NODE_STUB_VERSION"] = version
                result = self.run_setup("00-install-kali-packages.sh")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Node.js 20 or later is required", result.stderr)

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

    def test_simblock_falls_back_from_java17_or_missing_home(self):
        java17 = self.jdk("java17", "17.0.16")
        for java_home in (str(java17), str(self.directory / "missing"), ""):
            with self.subTest(java_home=java_home):
                self.env["JAVA_HOME"] = java_home
                result = self.run_setup("03-install-simblock.sh")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"gradlew clean: {self.java11}", self.commands())
                self.assertIn(f"gradlew build: {self.java11}", self.commands())

    def test_simblock_rejects_java11_runtime_without_compiler(self):
        (self.java11 / "bin" / "javac").unlink()
        result = self.run_setup("03-install-simblock.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("A Java 11 JDK was not found", result.stderr)
        self.assertNotIn("gradlew", self.commands())


if __name__ == "__main__":
    unittest.main()
