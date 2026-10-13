# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from mo_arbor.code_system_file import parse
from mo_arbor.diff import Diff
from mo_arbor.diff import diff
from tests.helpers import file
from tests.helpers import row

ROOT_A = parse(file(row("R"), row("A", parent="R")))


def test_no_previous_dump_means_everything_is_added() -> None:
    assert diff(None, ROOT_A) == Diff(added={"R", "A"}, changed=set(), removed=set())


def test_identical_dumps() -> None:
    assert diff(ROOT_A, ROOT_A) == Diff(added=set(), changed=set(), removed=set())


def test_added_and_removed() -> None:
    new = parse(file(row("R"), row("B", parent="R")))
    assert diff(ROOT_A, new) == Diff(added={"B"}, changed=set(), removed={"A"})


def test_changed() -> None:
    old = parse(
        file(row("R"), row("A", parent="R"), row("B", parent="R"), row("C", parent="R"))
    )
    new = parse(
        file(
            row("R"),
            row("A", parent="R", name="Renamed"),
            row("B", parent="R", validity_from="2025-01-09"),
            row("C", parent="R", validity_to="2026-05-31"),
        )
    )
    assert diff(old, new) == Diff(added=set(), changed={"A", "B", "C"}, removed=set())


def test_renamed_parent_does_not_change_its_children() -> None:
    new = parse(file(row("R", name="Renamed"), row("A", parent="R")))
    assert diff(ROOT_A, new) == Diff(added=set(), changed={"R"}, removed=set())


def test_moved_start_changes_the_children_it_clamps() -> None:
    """A's own row is unchanged, but its start is clamped to R's later one."""
    new = parse(file(row("R", validity_from="2020-01-01"), row("A", parent="R")))
    assert diff(ROOT_A, new) == Diff(added=set(), changed={"R", "A"}, removed=set())
