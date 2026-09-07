#!/usr/bin/env python3
"""Prove the vale sync wrapper retries a transient failure.

Each case puts a stub `vale` first on PATH. The stub counts its own calls in
a file, so the test can assert how many attempts the script made.
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "vale_sync.sh"

# Fails on every call until the counter reaches THRESHOLD, then succeeds.
STUB = """#!/usr/bin/env bash
count_file="$STUB_COUNT"
count=$(( $(cat "$count_file") + 1 ))
echo "$count" > "$count_file"
if [ "$count" -lt "$STUB_THRESHOLD" ]; then
  echo "could not fetch 'Google.zip' (status code '504')" >&2
  exit 1
fi
exit 0
"""


class ValeSyncTest(unittest.TestCase):
    def run_script(self, threshold: int, attempts: int = 3):
        """Run the wrapper against a stub that fails until `threshold`."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stub = root / "vale"
            stub.write_text(STUB, encoding="utf-8")
            stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
            counter = root / "count"
            counter.write_text("0", encoding="utf-8")

            env = dict(os.environ)
            env["PATH"] = f"{root}{os.pathsep}{env['PATH']}"
            env["STUB_COUNT"] = str(counter)
            env["STUB_THRESHOLD"] = str(threshold)
            env["VALE_SYNC_ATTEMPTS"] = str(attempts)
            # Keep the suite fast. The wait still doubles between attempts.
            env["VALE_SYNC_WAIT"] = "0"

            result = subprocess.run(
                ["bash", str(SCRIPT)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            return result, int(counter.read_text(encoding="utf-8"))

    def test_a_clean_sync_runs_once(self) -> None:
        result, calls = self.run_script(threshold=1)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(1, calls)

    def test_one_transient_failure_is_absorbed(self) -> None:
        result, calls = self.run_script(threshold=2)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(2, calls)
        self.assertIn("Retrying", result.stderr)

    def test_the_last_attempt_still_succeeds(self) -> None:
        result, calls = self.run_script(threshold=3)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(3, calls)

    def test_a_lasting_outage_still_fails(self) -> None:
        result, calls = self.run_script(threshold=99)
        self.assertEqual(1, result.returncode)
        self.assertEqual(3, calls)
        self.assertIn("failed after 3 attempts", result.stderr)

    def test_the_vale_output_reaches_the_log(self) -> None:
        """The reader needs the package and the status code, not just the
        wrapper's own message."""
        result, _ = self.run_script(threshold=99)
        self.assertIn("status code '504'", result.stderr)

    def test_the_attempt_count_is_configurable(self) -> None:
        result, calls = self.run_script(threshold=99, attempts=5)
        self.assertEqual(1, result.returncode)
        self.assertEqual(5, calls)


if __name__ == "__main__":
    unittest.main(verbosity=2)
