# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
"""SOR IDs.

See "Opbygning af SOR-id'er" under "Mere om SOR" on
https://sundhedsdatastyrelsen.dk/data-og-registre/nationale-sundhedsregistre/sundhedsvaesenets-organisationsregister/om-sor
"""

from pydantic import ConstrainedStr
from pydantic import Field
from stdnum import verhoeff

from mo_arbor.code_system_file import Row
from mo_arbor.code_system_file import Rows


class SorKey(ConstrainedStr):
    """A SOR ID, checked when pydantic reads it."""

    strip_whitespace = True
    # A running number of any length, the SOR namespace 1000016, the partition
    # ID 00 and a Verhoeff check digit. pydantic matches from the start of the
    # code, so the $ makes it match the whole code.
    regex = r"[1-9]\d*100001600\d$"

    @classmethod
    def validate(cls, value: str) -> str:
        value = super().validate(value)
        if not verhoeff.is_valid(value):
            raise ValueError("invalid SOR ID check digit")
        return value


class SorRow(Row):
    """A row of a SOR file, whose codes are SOR IDs."""

    # Fields given again lose their aliases
    user_key: SorKey = Field(alias="kode")
    parent_user_key: SorKey | None = Field(..., alias="kode_parent")


class SorRows(Rows):
    __root__: tuple[SorRow, ...]
