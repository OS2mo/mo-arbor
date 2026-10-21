# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from pydantic import ValidationError
from pydantic import parse_obj_as

from mo_arbor.sor import SorKey


@pytest.mark.parametrize(
    "code",
    [
        # Made-up codes in the shape of real ones, with valid check digits
        "1001000016005",
        "100001000016006",
        "1000001000016004",
    ],
)
def test_sor_key(code: str) -> None:
    assert parse_obj_as(SorKey, f" {code} ") == code


@pytest.mark.parametrize(
    "code",
    [
        # As Excel with Danish settings saves a 13-digit code
        "1,001E+12",
        # 1000001000016004 as Excel saves it, with the 16th digit zeroed
        "1000001000016000",
        # The last digit changed from 5 to 6
        "1001000016006",
        "123",
        # Without the SOR namespace
        "1234567890123",
        # A SOR ID with digits after it, which keep the check digit valid
        "100100001600508",
        "",
    ],
)
def test_not_a_sor_key(code: str) -> None:
    with pytest.raises(ValidationError):
        parse_obj_as(SorKey, code)
