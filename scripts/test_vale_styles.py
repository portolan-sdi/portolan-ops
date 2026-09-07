#!/usr/bin/env python3
"""Exercise every custom Vale rule with text that must pass and fail."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".vale.ini"


def words(count: int) -> str:
    """Return one sentence with exactly `count` words."""
    return " ".join(["word"] * count) + "."


CASES = {
    "Portolan-Blog.Sentence45": (
        "src/content/blog/post.mdx",
        words(46),
        words(45),
    ),
    "Portolan-Docs.Sentence30": ("page.md", words(31), words(30)),
    "Portolan-Mechanics.Ellipsis": ("page.md", "Wait...", "Wait."),
    "Portolan-Mechanics.EmDash": ("page.md", "word—word", "word — word"),
    "Portolan-Mechanics.EmDashDensity": (
        "page.md",
        "a — b — c — d — e",
        "a — b — c — d",
    ),
    "Portolan-Mechanics.Headings": (
        "page.md",
        "# Bad Heading Here",
        "# Good heading",
    ),
    "Portolan-Mechanics.Oxford": (
        "page.md",
        "Choose red, blue and green options.",
        "Choose red, blue, and green options.",
    ),
    "Portolan-Mechanics.Quotes": ("page.md", "“quoted”", '"quoted"'),
    "Portolan-Terms.AiReady": (
        "page.md",
        "Portolan is AI-first.",
        "Portolan is AI-ready.",
    ),
    "Portolan-Terms.Casing": ("page.md", "Geoparquet", "GeoParquet"),
    "Portolan-Terms.Formats": (
        "page.md",
        "Portolan uses Zarr.",
        "Support for Zarr is planned.",
    ),
    "Portolan-Terms.Hype": ("page.md", "A seamless tool.", "A direct tool."),
    "Portolan-Terms.Parts": ("page.md", "Rashid checks it.", "rashid checks it."),
    "Portolan-Terms.Spec": (
        "page.md",
        "Portolan is a standard.",
        "Portolan is a specification.",
    ),
    "Portolan-Terms.Urls": (
        "page.md",
        "https://portolan-one.vercel.app",
        "https://www.portolan-sdi.org/",
    ),
    "Portolan-Voice.ChatbotResidue": (
        "page.md",
        "I hope this helps.",
        "The command prints the result.",
    ),
    "Portolan-Voice.AffirmativeNegativeEcho": (
        "page.md",
        "It reads the policy. It does not read the answers.",
        "Although it reads the policy, the answers remain unavailable.",
    ),
    "Portolan-Voice.SerialListCadence": (
        "page.md",
        (
            "It reads red, blue, and green files. It writes one, two, and three. "
            "It logs the date, the size, and the name."
        ),
        (
            "It reads red, blue, and green files. It writes one, two, and three. "
            "It logs the name with the date and the size."
        ),
    ),
    "Portolan-Voice.ClosingTail": (
        "page.md",
        "In conclusion, publish the files.",
        "Publish the files.",
    ),
    "Portolan-Voice.ConsequenceCadence": (
        "page.md",
        "It is indexed, so people can search. It is open, so people can query.",
        "It is indexed, so people can search. People query the open files.",
    ),
    "Portolan-Voice.ContrastSlogan": (
        "page.md",
        "It is not just a report, but a complete transformation.",
        "The report includes the measured results.",
    ),
    "Portolan-Voice.DramaticColon": (
        "page.md",
        "Remember: this changes the final result.",
        "Remember that this changes the result.",
    ),
    "Portolan-Voice.Filler": ("page.md", "It basically works.", "It works."),
    "Portolan-Voice.Mirrored": (
        "page.md",
        "Published by anyone, discoverable by everyone.",
        "Publishers submit catalogs that the registry makes searchable.",
    ),
    "Portolan-Voice.Passive": (
        "page.md",
        "The file was written yesterday.",
        "The publisher wrote the file yesterday.",
    ),
    "Portolan-Voice.SoYouCan": (
        "page.md",
        "It is open, so you can read it.",
        "Because it is open, you can read it.",
    ),
    "Portolan-Voice.StockTransitions": (
        "page.md",
        "In today's landscape, catalogs matter.",
        "Catalogs make distributed data searchable.",
    ),
    "Portolan-Web.Absolutes": (
        ".vale-web/messages.md",
        "Everything works.",
        "The catalog works.",
    ),
    "Portolan-Web.Sentence30": (
        ".vale-web/messages.md",
        words(31),
        words(30),
    ),
}


class ValeStyleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("vale") is None:
            raise unittest.SkipTest("vale is not installed")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def checks(self, text: str, relative: str) -> set[str]:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text + "\n", encoding="utf-8")
        result = subprocess.run(
            [
                "vale",
                "--config",
                str(CONFIG),
                "--minAlertLevel",
                "suggestion",
                "--output",
                "JSON",
                relative,
            ],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )
        report = json.loads(result.stdout or "{}")
        return {alert["Check"] for alerts in report.values() for alert in alerts}

    def test_rule_inventory_matches_the_corpus(self) -> None:
        rules = {
            f"{path.parent.name}.{path.stem}"
            for path in (ROOT / "styles").glob("Portolan-*/*.yml")
        }
        self.assertEqual(rules, set(CASES))

    def test_each_rule_reports_its_bad_example(self) -> None:
        for check, (relative, bad, _good) in CASES.items():
            with self.subTest(check=check):
                self.assertIn(check, self.checks(bad, relative))

    def test_each_rule_accepts_its_good_example(self) -> None:
        for check, (relative, _bad, good) in CASES.items():
            with self.subTest(check=check):
                self.assertNotIn(check, self.checks(good, relative))

    def test_microsoft_package_is_active(self) -> None:
        self.assertIn(
            "Microsoft.Wordiness",
            self.checks("Tools utilize the cached file.", "page.md"),
        )

    def test_ai_tells_package_is_active(self) -> None:
        self.assertIn(
            "ai-tells.FigurativeCarries",
            self.checks("Every collection directory carries a manifest.", "page.md"),
        )

    def test_conflicting_ai_tells_rules_are_off(self) -> None:
        # Each probe reports its rule when the rule runs. .vale.ini states
        # the reason for every disable.
        probes = {
            "ai-tells.EmDashUsage": "The file—the one it wrote—holds the record.",
            "ai-tells.SemicolonUsage": "The check runs; the report follows.",
            "ai-tells.NegatedObject": "The tool makes no network calls.",
            "ai-tells.FormalRegister": "The CLI implements the specification.",
            "ai-tells.ColonUsage": "**Note:** Like this.",
            "ai-tells.DoubleHyphen": "Run portolan check --fix now.",
        }
        for check, text in probes.items():
            with self.subTest(check=check):
                self.assertNotIn(check, self.checks(text, "page.md"))

    def test_local_em_dash_rule_still_owns_the_em_dash(self) -> None:
        self.assertIn(
            "Portolan-Mechanics.EmDash",
            self.checks("The file—the one it wrote—holds it.", "page.md"),
        )

    def test_ai_tells_applies_to_the_blog_and_the_website(self) -> None:
        figurative = "Every collection directory carries a manifest."
        for relative in ("src/content/blog/post.mdx", ".vale-web/messages.md"):
            with self.subTest(path=relative):
                self.assertIn(
                    "ai-tells.FigurativeCarries", self.checks(figurative, relative)
                )
                self.assertNotIn(
                    "ai-tells.FormalRegister",
                    self.checks("The CLI implements the specification.", relative),
                )

    def test_the_ops_sync_block_is_ignored(self) -> None:
        block = (
            "<!-- ops-sync:begin — synced from portolan-sdi/portolan-ops. -->\n"
            "Every collection directory carries a manifest.\n"
            "<!-- ops-sync:end -->\n"
        )
        self.assertNotIn("ai-tells.FigurativeCarries", self.checks(block, "page.md"))

    def test_only_selected_readability_metrics_are_active(self) -> None:
        sentence = (
            "Administrative interoperability documentation complicates implementation."
        )
        dense = " ".join([sentence] * 20)
        readability = {
            check
            for check in self.checks(dense, "page.md")
            if check.startswith("Readability.")
        }
        self.assertEqual(
            readability,
            {
                "Readability.AutomatedReadability",
                "Readability.FleschReadingEase",
            },
        )

    def test_filler_allows_a_concrete_not_just_contrast(self) -> None:
        self.assertNotIn(
            "Portolan-Voice.Filler",
            self.checks("The scanner checks content, not just paths.", "page.md"),
        )

    def test_dramatic_colon_allows_a_stage_label(self) -> None:
        self.assertNotIn(
            "Portolan-Voice.DramaticColon",
            self.checks("**Stage 3: field matching.** Apply the rule.", "page.md"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
