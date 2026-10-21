# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
"""Build code system files for tests."""

import csv
import io

COLUMNS = [
    "kode",
    "kode_parent",
    "gyldig_fra",
    "gyldig_til",
    "navn",
    "type",
    "niveau",
    "aktiv",
    "dw_is_deleted",
    "dw_timestamp_insert",
    "dw_timestamp_update",
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
    such as aktiv.
    """
    return {
        "kode": user_key,
        "kode_parent": parent,
        "gyldig_fra": validity_from,
        "gyldig_til": validity_to,
        "navn": name,
        "type": org_unit_type,
        "niveau": org_unit_level,
        "aktiv": "true",
        "dw_is_deleted": "false",
        "dw_timestamp_insert": "2026-04-29T08:24:33",
        "dw_timestamp_update": "2026-07-12T02:01:15",
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
