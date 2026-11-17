# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
"""The report of how the code systems' units link to a target tree.

In MO, a code system's unit is related to units of an administrative tree
(Adm), which are related to units of a target tree. The report has a row for each
such chain, code system unit -> Adm unit -> target unit, so it
is always clear which target unit belongs to which Adm unit. A chain that stops
early has empty fields for the rest.
"""

import csv
import io
from collections.abc import Sequence
from datetime import datetime
from operator import attrgetter
from uuid import UUID

from pydantic import BaseModel

from mo_arbor.config import CodeSystem


class ReportUnit(BaseModel, frozen=True):
    uuid: UUID
    user_key: str
    name: str


class Systems(BaseModel, frozen=True):
    """The names of the systems in the report, as their roots are named in MO."""

    source: str
    adm: str
    target: str


class Chain(BaseModel, frozen=True):
    """A row of the report, which may stop after its source or Adm unit."""

    source: ReportUnit
    adm: ReportUnit | None
    target: ReportUnit | None


def by_user_key(units: list[ReportUnit]) -> list[ReportUnit]:
    return sorted(units, key=attrgetter("user_key"))


def chains(
    sources: list[ReportUnit],
    adm_units: dict[UUID, ReportUnit],
    target_units: dict[UUID, ReportUnit],
    related: dict[UUID, set[UUID]],
) -> list[Chain]:
    """The chains from each of the code system's units, the sources.

    `related` has each unit's related units. Sorted by code, so a report
    without changes is the same file, and is easy to read.
    """

    def linked(
        unit: ReportUnit | None, units: dict[UUID, ReportUnit]
    ) -> Sequence[ReportUnit | None]:
        """The unit's related units among `units`.

        [None] if there are none, or no unit, so the chain stops there and has
        None for the rest.
        """
        if unit is None:
            return [None]
        found = [units[r] for r in related.get(unit.uuid, ()) if r in units]
        return by_user_key(found) or [None]

    return [
        Chain(source=source, adm=adm, target=target)
        for source in by_user_key(sources)
        for adm in linked(source, adm_units)
        for target in linked(adm, target_units)
    ]


def to_csv(systems: Systems, rows: list[Chain]) -> bytes:
    """The report as agreed with its receiver.

    UTF-8 without a byte order mark, `;` as separator, as names often have
    commas, every field quoted with `"` doubled inside (RFC 4180), and CRLF.
    """
    out = io.StringIO()
    writer = csv.writer(
        out, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\r\n"
    )
    writer.writerow(
        [
            "Source_System",
            "Source_Code",
            "Source_Name",
            "Adm_System",
            "Adm_Code",
            "Adm_Name",
            "Target_System",
            "Target_Code",
            "Target_Name",
        ]
    )
    for row in rows:
        source, adm, target = row.source, row.adm, row.target
        writer.writerow(
            [
                systems.source,
                source.user_key,
                source.name,
                systems.adm if adm else "",
                adm.user_key if adm else "",
                adm.name if adm else "",
                systems.target if target else "",
                target.user_key if target else "",
                target.name if target else "",
            ]
        )
    return out.getvalue().encode("utf-8")


def report_file_name(code_system: CodeSystem, time: datetime) -> str:
    """E.g. sor_relations_20261117_120000.csv.

    The code system's name comes first, so the file is not taken for one of
    its dumps, which end in the name and the time.
    """
    return f"{code_system.name}_relations_{time:%Y%m%d_%H%M%S}.csv"
