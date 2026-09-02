#!/usr/bin/env python3
"""Tests for vale_messages.py."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import vale_messages as vm


class LeavesTest(unittest.TestCase):
    def test_returns_only_string_leaves(self) -> None:
        data = {"hero": {"title": "Hello", "count": 2}, "items": ["skip"]}
        self.assertEqual(vm.leaves(data), [("hero.title", "Hello")])


class ExtractTest(unittest.TestCase):
    def test_strips_tags_and_flattens_newlines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "en.json"
            source.write_text(
                json.dumps({"hero": {"body": "Read <m>remote\n data</m>."}}),
                encoding="utf-8",
            )
            out_dir = root / ".vale-web"
            with (
                patch.object(vm, "OUT_DIR", out_dir),
                patch.object(vm, "OUT_FILE", out_dir / "messages.md"),
                patch.object(vm, "MAP_FILE", out_dir / "messages.map.json"),
            ):
                self.assertEqual(vm.extract(source), 0)
                text = vm.OUT_FILE.read_text(encoding="utf-8")
                mapping = json.loads(vm.MAP_FILE.read_text(encoding="utf-8"))

        self.assertEqual(text, "Read remote data.\n\n")
        self.assertEqual(mapping["lines"], {"1": "hero.body", "2": "hero.body"})


class RemapTest(unittest.TestCase):
    def test_prints_the_source_key(self) -> None:
        report = {
            ".vale-web/messages.md": [
                {"Line": 1, "Check": "Portolan-Terms.Spec", "Message": "Fix it."}
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            map_file = Path(tmp) / "messages.map.json"
            map_file.write_text(
                json.dumps({"source": "messages/en.json", "lines": {"1": "hero.body"}}),
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch.object(vm, "MAP_FILE", map_file), patch("sys.stdout", output):
                status = vm.remap(io.StringIO(json.dumps(report)))

        self.assertEqual(status, 1)
        self.assertEqual(
            output.getvalue(),
            "messages/en.json → hero.body:Portolan-Terms.Spec:Fix it.\n",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
