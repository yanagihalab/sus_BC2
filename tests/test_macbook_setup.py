"""Check MacBook setup orchestration with Docker stubbed, without network access."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "setup" / "macbook" / "macbook-docker-env.sh"


class MacBookSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        self.log = self.directory / "docker.jsonl"
        docker = self.bin / "docker"
        docker.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, pathlib, sys\n"
            "args = sys.argv[1:]\n"
            "record = {'args': args}\n"
            "if args[0] == 'build':\n"
            "    context = pathlib.Path(args[-1])\n"
            "    record['dockerfile'] = sys.stdin.read()\n"
            "    record['context_files'] = sorted(str(p.relative_to(context)) for p in context.rglob('*'))\n"
            "    record['package_script'] = (context / '00-install-kali-packages.sh').read_text()\n"
            "with open(os.environ['DOCKER_LOG'], 'a') as log:\n"
            "    log.write(json.dumps(record) + '\\n')\n"
            "if args[0] == 'build' and os.environ.get('FAIL_BUILD') == 'yes':\n"
            "    sys.exit(27)\n"
        )
        docker.chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "DOCKER_LOG": str(self.log),
            "TMPDIR": str(self.directory),
            "IMAGE_NAME": "stub-kali-image",
            "RUN_VERIFY": "no",
            "RUN_AMD64_INJECTIVE_CHECK": "no",
            "FAIL_BUILD": "no",
        }

    def run_setup(self):
        return subprocess.run(
            ["bash", str(SCRIPT)],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=15,
        )

    def records(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_image_uses_common_packages_from_minimal_context(self):
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        records = self.records()
        build = next(record for record in records if record["args"][0] == "build")
        self.assertEqual(build["context_files"], ["00-install-kali-packages.sh"])
        self.assertEqual(
            build["package_script"],
            (ROOT / "setup" / "normal" / "00-install-kali-packages.sh").read_text(),
        )
        self.assertIn("COPY 00-install-kali-packages.sh /tmp/00-install-kali-packages.sh", build["dockerfile"])
        self.assertIn("RUN SETUP_DOCKER=no SETUP_SSH=no bash /tmp/00-install-kali-packages.sh", build["dockerfile"])
        self.assertNotIn("apt update", build["dockerfile"])
        self.assertNotIn("apt install", build["dockerfile"])
        self.assertFalse(Path(build["args"][-1]).exists())
        self.assertFalse(any(record["args"][0] == "run" for record in records))

    def test_build_failure_removes_context_and_stops(self):
        self.env["FAIL_BUILD"] = "yes"
        self.env["RUN_VERIFY"] = "yes"
        result = self.run_setup()
        self.assertEqual(result.returncode, 27)
        records = self.records()
        build = next(record for record in records if record["args"][0] == "build")
        self.assertFalse(Path(build["args"][-1]).exists())
        self.assertFalse(any(record["args"][0] == "run" for record in records))

    def test_optional_amd64_check_installs_dependencies_before_injective(self):
        self.env["RUN_AMD64_INJECTIVE_CHECK"] = "yes"
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        run = next(record for record in self.records() if record["args"][0] == "run")
        self.assertIn("linux/amd64", run["args"])
        self.assertIn("kalilinux/kali-rolling", run["args"])
        command = run["args"][-1]
        self.assertIn("set -euo pipefail", command)
        self.assertIn("SETUP_DOCKER=no SETUP_SSH=no bash ./setup/normal/00-install-kali-packages.sh", command)
        self.assertLess(command.index("00-install-kali-packages.sh"), command.index("04-install-injectived.sh"))
        self.assertIn("WORKDIR=/tmp", command)

    def test_verification_uses_built_image(self):
        self.env["RUN_VERIFY"] = "yes"
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        run = next(record for record in self.records() if record["args"][0] == "run")
        self.assertIn("stub-kali-image", run["args"])
        self.assertIn(f"{ROOT}:/work", run["args"])


if __name__ == "__main__":
    unittest.main()
