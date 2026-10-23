"""Prove scripts/lychee.sh builds the lychee command the fleet relies on.

Most cases set LYCHEE_BIN to a stub that records its arguments, so the test
needs no network and no real lychee. The checksum case puts a stub `curl`
first on PATH that downloads the wrong bytes.

Run directly (check.yml does):

    python3 scripts/test_lychee.py
"""

from __future__ import annotations

import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "lychee.sh"
SUMS = ROOT / "scripts" / "lychee_sums.sh"
TRIPLES = (
    "x86_64-unknown-linux-gnu",
    "aarch64-unknown-linux-gnu",
    "x86_64-apple-darwin",
    "aarch64-apple-darwin",
)
HOOKS = ROOT / ".pre-commit-hooks.yaml"
OPS_CONFIG = ROOT / ".pre-commit-config.yaml"

# Writes one argument per line, then exits with STUB_EXIT.
LYCHEE_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$STUB_ARGS"
exit "${STUB_EXIT:-0}"
"""

# Writes junk to the --output path, as a tampered download would.
CURL_STUB = """#!/usr/bin/env bash
while [ "$#" -gt 0 ]; do
  if [ "$1" = --output ]; then echo junk > "$2"; fi
  shift
done
"""


def executable(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


class WrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.work = self.root / "repo"
        self.work.mkdir()
        self.args_file = self.root / "args"
        stub = executable(self.root / "lychee", LYCHEE_STUB)
        self.env = dict(os.environ)
        self.env.pop("LYCHEE_ROOT_DIR", None)
        self.env["LYCHEE_BIN"] = str(stub)
        self.env["STUB_ARGS"] = str(self.args_file)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_script(self, *args: str, **env: str) -> tuple[int, list[str]]:
        result = subprocess.run(
            ["bash", str(SCRIPT), *args],
            cwd=self.work,
            env={**self.env, **env},
            capture_output=True,
            text=True,
            check=False,
        )
        lines = self.args_file.read_text(encoding="utf-8").splitlines()
        return result.returncode, lines

    def configs(self, args: list[str]) -> list[str]:
        return [args[i + 1] for i, arg in enumerate(args) if arg == "--config"]

    def root_dir(self, args: list[str]) -> str:
        return args[args.index("--root-dir") + 1]

    def test_the_org_rules_always_load(self) -> None:
        _, args = self.run_script(".")
        self.assertEqual(self.configs(args), [str(ROOT / "lychee" / "org.toml")])

    def test_the_repo_rules_load_after_the_org_rules(self) -> None:
        # lychee merges arrays, and a later file wins on a scalar key. The
        # repo file must come second to override the org file.
        (self.work / "lychee.toml").write_text("", encoding="utf-8")
        _, args = self.run_script(".")
        self.assertEqual(
            self.configs(args), [str(ROOT / "lychee" / "org.toml"), "lychee.toml"]
        )

    def test_the_root_is_the_working_directory(self) -> None:
        _, args = self.run_script(".")
        self.assertEqual(self.root_dir(args), str(self.work.resolve()))

    def test_the_root_is_public_when_it_exists(self) -> None:
        # Vite and Next.js serve public/ at /, so /logo.svg lives there.
        (self.work / "public").mkdir()
        _, args = self.run_script(".")
        self.assertEqual(self.root_dir(args), str(self.work.resolve() / "public"))

    def test_an_explicit_root_wins(self) -> None:
        (self.work / "public").mkdir()
        site = self.root / "site"
        site.mkdir()
        _, args = self.run_script(".", LYCHEE_ROOT_DIR="../site")
        self.assertEqual(self.root_dir(args), str(site.resolve()))

    def test_arguments_pass_through_last(self) -> None:
        _, args = self.run_script("--offline", "README.md", "docs/a.md")
        self.assertEqual(args[-3:], ["--offline", "README.md", "docs/a.md"])

    def test_the_lychee_exit_code_passes_through(self) -> None:
        # The workflow tells broken links (2) from a bad config (3).
        for code in ("0", "2", "3"):
            status, _ = self.run_script(".", STUB_EXIT=code)
            self.assertEqual(status, int(code))


class DownloadTest(unittest.TestCase):
    def test_a_wrong_checksum_stops_the_run(self) -> None:
        if os.uname().sysname != "Linux" or os.uname().machine != "x86_64":
            self.skipTest("the pinned sums are per platform")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            executable(bin_dir / "curl", CURL_STUB)
            cache = root / "cache"
            env = dict(os.environ)
            env.pop("LYCHEE_BIN", None)
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["LYCHEE_CACHE_DIR"] = str(cache)
            result = subprocess.run(
                ["bash", str(SCRIPT), "--version"],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("checksum mismatch", result.stderr)
            self.assertEqual(list(cache.rglob("lychee")), [])


# Prints a sum built from the triple in the requested URL, in the
# `sha256sum` format of the release assets.
SUMS_CURL_STUB = """#!/usr/bin/env bash
for arg in "$@"; do url=$arg; done
echo "$url" >> "$STUB_URLS"
case "$url" in
  *x86_64-unknown-linux-gnu*) c=1 ;;
  *aarch64-unknown-linux-gnu*) c=2 ;;
  *x86_64-apple-darwin*) c=3 ;;
  *aarch64-apple-darwin*) c=4 ;;
esac
printf '%s  lychee.tar.gz\\n' "$(printf "$c%.0s" $(seq 64))"
"""


class SumsTest(unittest.TestCase):
    """scripts/lychee_sums.sh keeps the pinned sums in step with the version."""

    def test_the_sums_follow_a_version_bump(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            executable(bin_dir / "curl", SUMS_CURL_STUB)
            copy = root / "lychee.sh"
            text = SCRIPT.read_text(encoding="utf-8")
            copy.write_text(
                re.sub(
                    r"^LYCHEE_VERSION=.*$",
                    "LYCHEE_VERSION=9.9.9",
                    text,
                    flags=re.MULTILINE,
                ),
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["STUB_URLS"] = str(root / "urls")
            subprocess.run(
                ["bash", str(SUMS), str(copy)], env=env, check=True, capture_output=True
            )
            result = copy.read_text(encoding="utf-8")
            for digit, triple in enumerate(TRIPLES, start=1):
                block = result.split(f"    {triple})\n", 1)[1].splitlines()[0]
                self.assertIn(str(digit) * 64, block, triple)
            self.assertIn("release lychee-v9.9.9.", result)
            urls = (root / "urls").read_text(encoding="utf-8").splitlines()
            self.assertTrue(all("/lychee-v9.9.9/" in url for url in urls))
            self.assertEqual(len(urls), len(TRIPLES))

    def test_every_pinned_triple_is_refreshed(self) -> None:
        # A triple added to target() without a refresh would keep a stale sum.
        pinned = re.findall(
            r"^    ([a-z0-9_-]+)\)$", SCRIPT.read_text(), flags=re.MULTILINE
        )
        self.assertEqual(sorted(pinned), sorted(TRIPLES))


class HookTest(unittest.TestCase):
    """Ops runs a local copy of the hook it ships. They must not drift."""

    def test_the_local_copy_matches_the_shipped_hook(self) -> None:
        shipped = {hook["id"]: hook for hook in yaml.safe_load(HOOKS.read_text())}
        ops = yaml.safe_load(OPS_CONFIG.read_text())
        local = {
            hook["id"]: hook
            for repo in ops["repos"]
            if repo["repo"] == "local"
            for hook in repo["hooks"]
        }
        keys = ("entry", "language", "args", "types_or", "require_serial")
        for key in keys:
            self.assertEqual(local["lychee"].get(key), shipped["lychee"].get(key), key)

    def test_the_hook_never_touches_the_network(self) -> None:
        shipped = {hook["id"]: hook for hook in yaml.safe_load(HOOKS.read_text())}
        self.assertIn("--offline", shipped["lychee"]["args"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
