# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from datetime import datetime
from uuid import uuid4

import pytest

from mo_arbor.mo import depths
from mo_arbor.mo import mo_datetime
from mo_arbor.mo import unit_end

NAME_CHANGE = mo_datetime(date(2027, 1, 1))
END = mo_datetime(date(2031, 1, 1))


@pytest.mark.parametrize(
    "period_ends,expected",
    [
        ({None}, None),
        ({NAME_CHANGE}, NAME_CHANGE.date()),
        ({END}, END.date()),
        # A planned change ends the current period, not the unit
        ({NAME_CHANGE, END}, END.date()),
        ({NAME_CHANGE, None}, None),
        ({NAME_CHANGE, END, None}, None),
    ],
)
def test_unit_end(period_ends: set[datetime | None], expected: date | None) -> None:
    assert unit_end(period_ends) == expected


def test_depths() -> None:
    """A unit whose parent is not among them is at the top."""
    root, child, grandchild, other = uuid4(), uuid4(), uuid4(), uuid4()
    parents = {root: None, child: root, grandchild: child, other: uuid4()}
    assert depths(parents) == {root: 1, child: 2, grandchild: 3, other: 1}
