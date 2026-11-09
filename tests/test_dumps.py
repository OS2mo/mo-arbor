# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import base64
from datetime import UTC
from datetime import datetime

import pytest

from mo_arbor.code_system_file import InvalidFile
from mo_arbor.dumps import DumpFile
from mo_arbor.dumps import DumpNotFound
from mo_arbor.dumps import DumpStore
from mo_arbor.dumps import decode


@pytest.mark.parametrize(
    "file_name,expected",
    [
        pytest.param(
            "region_sor_20261007_153900.csv",
            # File names have no time zone
            datetime(2026, 10, 7, 15, 39),
            id="dump",
        ),
        pytest.param(
            "sor_20261007_153900.csv", datetime(2026, 10, 7, 15, 39), id="no-prefix"
        ),
        pytest.param("region_sor_udtraek.csv", None, id="no-time"),
        pytest.param("region_xsor_20261007_153900.csv", None, id="other-name"),
        pytest.param("region_sor_20261007_153900.txt", None, id="not-csv"),
        pytest.param("region_okosted_20261007_153900.csv", None, id="other-system"),
        pytest.param("region_sor_20260231_000000.csv", None, id="invalid-date"),
    ],
)
def test_dump_time(file_name: str, expected: datetime | None) -> None:
    assert DumpStore("sor").dump_time(file_name) == expected


def test_newest_dump() -> None:
    """By the time in the name, not when the file was written."""
    written = datetime(2026, 11, 1, tzinfo=UTC)
    morning = DumpFile(file_name="region_sor_20260501_080000.csv", updated_at=written)
    evening = DumpFile(file_name="region_sor_20260501_200000.csv", updated_at=written)
    # Written last, but the oldest dump
    earlier = DumpFile(
        file_name="region_sor_20260430_120000.csv",
        updated_at=datetime(2026, 11, 2, tzinfo=UTC),
    )
    dumps = {d.file_name: d for d in [morning, evening, earlier]}
    assert DumpStore("sor").newest_dump(dumps) == evening


def test_newest_dump_without_dumps() -> None:
    with pytest.raises(DumpNotFound):
        DumpStore("sor").newest_dump({})


@pytest.mark.parametrize("contents", ["\ufeffSkovvej", "Skovvej"])
def test_decode_removes_byte_order_mark(contents: str) -> None:
    assert decode(base64.b64encode(contents.encode()).decode()) == "Skovvej"


def test_decode_rejects_other_encodings() -> None:
    with pytest.raises(InvalidFile):
        decode(base64.b64encode("Søvej".encode("latin-1")).decode())
