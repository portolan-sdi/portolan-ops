#!/usr/bin/env python3
"""Unit tests for build_agents_block.py.

Run directly (check.yml does):

    python3 scripts/test_build_agents_block.py
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_agents_block as bab


class AbsolutizeTest(unittest.TestCase):
    def test_relative_link_gains_the_ops_prefix(self):
        got = bab.absolutize("see [VOICE.md](VOICE.md) first")
        self.assertEqual(f"see [VOICE.md]({bab.BLOB}VOICE.md) first", got)

    def test_nested_path_is_rewritten(self):
        got = bab.absolutize("[AI policy](policies/AI_POLICY.md)")
        self.assertIn(f"{bab.BLOB}policies/AI_POLICY.md", got)

    def test_absolute_link_is_left_alone(self):
        text = "[obstore](https://github.com/developmentseed/obstore)"
        self.assertEqual(text, bab.absolutize(text))

    def test_bare_anchor_is_left_alone(self):
        text = "[the budget](#writing-issues-and-pull-requests)"
        self.assertEqual(text, bab.absolutize(text))

    def test_bare_url_in_prose_is_left_alone(self):
        text = "The canonical homepage is https://www.portolan-sdi.org/."
        self.assertEqual(text, bab.absolutize(text))

    def test_image_is_left_alone(self):
        text = "![badge](img/badge.svg)"
        self.assertEqual(text, bab.absolutize(text))


class RenderTest(unittest.TestCase):
    def test_markers_wrap_the_body(self):
        out = bab.render("# Norms\n\nBe brief.\n")
        self.assertTrue(out.startswith(bab.BEGIN))
        self.assertIn(bab.END, out)
        self.assertIn("Be brief.", out)

    def test_body_sits_inside_the_markers(self):
        out = bab.render("# Norms\n\nBe brief.\n")
        inside = out.split(bab.BEGIN)[1].split(bab.END)[0]
        self.assertIn("Be brief.", inside)

    def test_repo_section_sits_outside_the_markers(self):
        out = bab.render("# Norms\n")
        after = out.split(bab.END)[1]
        self.assertIn("Repo-specific instructions", after)

    def test_render_is_idempotent(self):
        source = "# Norms\n\nSee [STYLE.md](STYLE.md).\n"
        self.assertEqual(bab.render(source), bab.render(source))


class GeneratedFileTest(unittest.TestCase):
    """The committed template must match what the generator produces."""

    def test_template_is_current(self):
        self.assertEqual(
            bab.TEMPLATE.read_text(encoding="utf-8"),
            bab.render(bab.SOURCE.read_text(encoding="utf-8")),
            "templates/repo/AGENTS.md is stale; "
            "run python3 scripts/build_agents_block.py",
        )

    def test_check_mode_agrees(self):
        self.assertEqual(0, bab.main(["--check"]))

    def test_no_bare_repo_relative_path_survives(self):
        """A backticked `brand/brand.json` reads as a local file downstream,
        where it does not exist. Every ops path must be a link, which the
        generator rewrites to an absolute URL."""
        template = bab.TEMPLATE.read_text(encoding="utf-8")
        bare = re.findall(r"`([a-z][\w./-]*/[\w./-]+\.\w{2,4})`", template)
        self.assertEqual(
            [],
            bare,
            f"write these as markdown links so they absolutize: {bare}",
        )

    def test_every_link_in_the_template_is_absolute(self):
        template = bab.TEMPLATE.read_text(encoding="utf-8")
        block = template.split(bab.END)[0]
        relative = [
            t
            for t in re.findall(r"\]\(([^)]+)\)", block)
            if not t.startswith(("http", "#", "mailto:"))
        ]
        self.assertEqual([], relative, f"relative links in the block: {relative}")

    def test_norms_reach_the_template_as_text(self):
        """The point of the whole exercise: rules, not a link list."""
        template = bab.TEMPLATE.read_text(encoding="utf-8")
        for phrase in (
            "two layers",
            "## What changed",
            "writing_check.py",
            "does not alter behavior",
            "ground truth for the Portolan standard",
            "verify it exists in the shipped tool",
            "say so and stop",
            "VOICE.md",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, template)

    def test_no_ops_vantage_referents_survive(self):
        """The block lands in other repos, where "this repo" and "here"
        resolve to the wrong place. Name portolan-ops instead."""
        template = bab.TEMPLATE.read_text(encoding="utf-8")
        block = template.split(bab.END)[0]
        prose = re.sub(r"<!--.*?-->", "", block, flags=re.DOTALL)
        for referent in ("this repo", "in this file", "change it here"):
            with self.subTest(referent=referent):
                self.assertNotIn(referent, prose)


if __name__ == "__main__":
    unittest.main(verbosity=2)
