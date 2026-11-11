# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
"""Helpers for tests."""

import csv
import io
from collections.abc import Awaitable
from collections.abc import Callable

# The integration tests' `upload_file` fixture, called with a file name and the
# file's contents
UploadFile = Callable[[str, str], Awaitable[None]]

COLUMNS = [
    "kode",
    "kode_parent",
    "gyldig_fra",
    "gyldig_til",
    "navn",
    "type",
    "niveau",
]

Row = dict[str, str]


def row(
    user_key: str,
    *,
    parent: str = "",
    validity_from: str = "2015-07-30",
    validity_to: str = "",
    name: str = "Unit",
    org_unit_type: str = "klinisk enhed",
    org_unit_level: str = "N1",
    **extra: str,
) -> Row:
    """Build a row like those in a real file.

    The arguments are named as the fields in MO. `extra` sets other columns,
    such as one the file should not have.
    """
    return {
        "kode": user_key,
        "kode_parent": parent,
        "gyldig_fra": validity_from,
        "gyldig_til": validity_to,
        "navn": name,
        "type": org_unit_type,
        "niveau": org_unit_level,
        **extra,
    }


def file(*rows: Row, columns: list[str] = COLUMNS) -> str:
    """Build a file quoted as in the spec, with CRLF as delivered."""
    out = io.StringIO()
    writer = csv.DictWriter(
        out,
        columns,
        delimiter=";",
        quoting=csv.QUOTE_ALL,
        lineterminator="\r\n",
        restval="",
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()
