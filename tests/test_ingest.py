# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from mo_arbor.code_system_file import Rows
from mo_arbor.diff import diff
from mo_arbor.ingest import TERMINATION_PRIORITY
from mo_arbor.ingest import priorities
from tests.helpers import file
from tests.helpers import row


def test_parents_first_and_terminations_last_children_first() -> None:
    old = Rows.parse(file(row("R"), row("A", parent="R"), row("B", parent="A")))
    # The root is renamed, C is added, and A and B are removed
    new = Rows.parse(file(row("R", name="Renamed"), row("C", parent="R")))

    assert priorities(diff(old, new), new, old) == {
        "R": 1,
        "C": 2,
        "A": TERMINATION_PRIORITY - 2,
        "B": TERMINATION_PRIORITY - 3,
    }
