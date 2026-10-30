# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from datetime import datetime

import pytest

from mo_arbor.mo import mo_datetime
from mo_arbor.mo import unit_end

NAME_CHANGE = mo_datetime(date(2027, 1, 1))
END = mo_datetime(date(2031, 1, 1))


@pytest.mark.parametrize(
    "period_ends,expected",
    [
        ([None], None),
        ([END], date(2031, 1, 1)),
        # A planned change ends the current period, not the unit
        ([NAME_CHANGE, END], date(2031, 1, 1)),
        ([END, NAME_CHANGE], date(2031, 1, 1)),
        ([NAME_CHANGE, None], None),
    ],
)
def test_unit_end(period_ends: list[datetime | None], expected: date | None) -> None:
    assert unit_end(period_ends) == expected
