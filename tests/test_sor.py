# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest

from mo_arbor.sor import is_sor_id


@pytest.mark.parametrize(
    "code,valid",
    [
        # Made-up codes in the shape of real ones, with valid check digits
        ("1001000016005", True),
        ("100001000016006", True),
        ("1000001000016004", True),
        # As Excel with Danish settings saves a 13-digit code
        ("1,001E+12", False),
        # 1000001000016004 as Excel saves it, with the 16th digit zeroed
        ("1000001000016000", False),
        # The last digit changed from 5 to 6
        ("1001000016006", False),
        ("123", False),
        # Without the SOR namespace
        ("1234567890123", False),
        ("", False),
    ],
)
def test_is_sor_id(code: str, valid: bool) -> None:
    assert is_sor_id(code) == valid
