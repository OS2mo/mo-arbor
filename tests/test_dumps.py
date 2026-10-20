# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime

import pytest

from mo_arbor.dumps import DumpStore

PATTERN = "region_sor_%Y%m%d_%H%M%S.csv"


@pytest.mark.parametrize(
    "file_name,expected",
    [
        pytest.param(
            "region_sor_20261007_153900.csv",
            # File names have no time zone
            datetime(2026, 10, 7, 15, 39),
            id="dump",
        ),
        pytest.param("region_sor_udtraek.csv", None, id="no-time"),
        pytest.param("region_okosted_20261007_153900.csv", None, id="other-system"),
        pytest.param("region_sor_20260231_000000.csv", None, id="invalid-date"),
    ],
)
def test_dump_time(file_name: str, expected: datetime | None) -> None:
    assert DumpStore(PATTERN).dump_time(file_name) == expected
