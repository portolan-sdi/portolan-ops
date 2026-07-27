#!/usr/bin/env python3
"""Tests for the sharding half of the synced mutation scripts.

The mutation job's whole-tree path is exercised end to end by
ci-selftest.yml against tests/fixture-package. Its sharded path cannot be:
the fixture holds one module, and a slice of one module is not a slice.

These cover the logic instead. Two properties matter beyond the obvious
cases, because the sharded floor in .mutation-shards.json is worthless if
either breaks:

  - Assignment does not depend on where the repo is checked out.
  - Adding a file moves that file only, leaving other files' slices alone.

mutation_score.py is covered by the fixture run, which reads a real stats
file and enforces a real floor.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import ClassVar

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "templates" / "repo" / "scripts")
)

from mutant_globs import main as globs_main
from mutant_globs import mutant_glob
from shard_select import select, shard_key, shard_of


class MutantGlobTest(unittest.TestCase):
    def test_flat_layout_becomes_a_dotted_module(self) -> None:
        self.assertEqual(
            mutant_glob("portolan_cli/backends/iceberg.py"),
            "portolan_cli.backends.iceberg.x*",
        )

    def test_src_layout_drops_the_src_prefix(self) -> None:
        # mutmut names mutants after the importable module, and `src` is a
        # directory rather than a package.
        self.assertEqual(mutant_glob("src/rashid/validate.py"), "rashid.validate.x*")

    def test_package_init_collapses_into_the_package(self) -> None:
        self.assertEqual(mutant_glob("src/rashid/__init__.py"), "rashid.x*")

    def test_backslashes_are_read_as_separators(self) -> None:
        self.assertEqual(mutant_glob(r"src\rashid\validate.py"), "rashid.validate.x*")

    def test_non_python_paths_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mutant_glob("README.md")

    def test_bare_init_is_rejected(self) -> None:
        # There is no package to name, so any glob would be wrong.
        with self.assertRaises(ValueError):
            mutant_glob("__init__.py")

    def test_no_arguments_is_a_failure(self) -> None:
        # An empty filter list makes mutmut test everything, which would
        # read as a covered shard.
        self.assertEqual(globs_main([]), 1)

    def test_glob_does_not_reach_into_submodules(self) -> None:
        # `rashid.*` would also match rashid.validate, inflating a shard with
        # mutants that belong to a different slice.
        self.assertTrue(mutant_glob("src/rashid/__init__.py").endswith(".x*"))


class ShardAssignmentTest(unittest.TestCase):
    PATHS: ClassVar[list[str]] = [f"pkg/module_{i}.py" for i in range(200)]

    def test_assignment_is_stable_across_calls(self) -> None:
        first = [shard_of(p, 25) for p in self.PATHS]
        second = [shard_of(p, 25) for p in self.PATHS]
        self.assertEqual(first, second)

    def test_assignment_stays_within_range(self) -> None:
        self.assertTrue(all(0 <= shard_of(p, 25) < 25 for p in self.PATHS))

    def test_shard_count_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            shard_of("pkg/a.py", 0)

    def test_every_path_lands_in_exactly_one_shard(self) -> None:
        seen: list[str] = []
        for shard in range(25):
            seen.extend(select(self.PATHS, 25, shard))
        self.assertEqual(sorted(seen), sorted(self.PATHS))

    def test_adding_a_file_leaves_the_others_where_they_were(self) -> None:
        # The reason assignment hashes the path instead of using its index
        # in a sorted list. Index assignment reshuffles everything on any
        # commit that adds a module, voiding every recorded shard rate.
        #
        # The new path has to sort near the front. A file that sorts last
        # shifts no index, so it would pass against index assignment too
        # and prove nothing.
        added = "pkg/aaa_first.py"
        self.assertLess(added, min(self.PATHS), "new path must sort first")
        before = {p: shard_of(p, 25) for p in self.PATHS}
        after = {p: shard_of(p, 25) for p in [added, *self.PATHS]}
        for path, shard in before.items():
            self.assertEqual(after[path], shard, path)

    def test_shards_are_not_wildly_uneven(self) -> None:
        # CRC-32 clustered these prefixes badly enough to leave one shard
        # with 17 files and another with 1, which is why this uses BLAKE2b.
        sizes = [len(select(self.PATHS, 25, s)) for s in range(25)]
        self.assertGreater(min(sizes), 0)
        self.assertLess(max(sizes), 3 * (len(self.PATHS) / 25))

    def test_selection_is_sorted(self) -> None:
        chosen = select(self.PATHS, 25, 3)
        self.assertEqual(chosen, sorted(chosen))

    def test_shard_index_must_be_in_range(self) -> None:
        with self.assertRaises(ValueError):
            select(self.PATHS, 25, 25)

    def test_key_ignores_where_the_repo_lives(self) -> None:
        # An absolute root made assignment depend on the checkout path, so
        # a CI runner and a laptop disagreed about every file's shard.
        here = shard_key(Path("src"), Path("src/rashid/validate.py"))
        elsewhere = shard_key(
            Path("/tmp/build/src"), Path("/tmp/build/src/rashid/validate.py")
        )
        self.assertEqual(here, elsewhere)
        self.assertEqual(here, "src/rashid/validate.py")


if __name__ == "__main__":
    unittest.main(verbosity=2)
