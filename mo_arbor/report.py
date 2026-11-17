# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
"""The report of how the code systems' units link to 8S.

In MO, a code system's unit is related to units of an administrative tree
(Adm), which are related to units of 8S's tree. The report has a row for each
such chain, code system unit -> Adm unit -> 8S unit, so it
is always clear which 8S unit belongs to which Adm unit. A chain that stops
early has empty fields for the rest.
"""

import csv
import io
from datetime import datetime
from operator import attrgetter
from uuid import UUID

from pydantic import BaseModel

from mo_arbor.config import CodeSystem

HEADER = [
    "Source_System",
    "Source_Code",
    "Source_Name",
    "Adm_Code",
    "Adm_Name",
    "Target_System",
    "Target_Code",
    "Target_Name",
]


class ReportUnit(BaseModel, frozen=True):
    uuid: UUID
    user_key: str
    name: str


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
    rows = []
    for source in by_user_key(sources):
        adms = [adm_units[r] for r in related.get(source.uuid, ()) if r in adm_units]
        if not adms:
            rows.append(Chain(source=source, adm=None, target=None))
        for adm in by_user_key(adms):
            targets = [
                target_units[r] for r in related.get(adm.uuid, ()) if r in target_units
            ]
            if not targets:
                rows.append(Chain(source=source, adm=adm, target=None))
            for target in by_user_key(targets):
                rows.append(Chain(source=source, adm=adm, target=target))
    return rows


def to_csv(code_system: CodeSystem, rows: list[Chain]) -> bytes:
    """The report as agreed with its receiver.

    UTF-8 without a byte order mark, `;` as separator, as names often have
    commas, every field quoted with `"` doubled inside (RFC 4180), and CRLF.
    """
    out = io.StringIO()
    writer = csv.writer(
        out, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\r\n"
    )
    writer.writerow(HEADER)
    for row in rows:
        source, adm, target = row.source, row.adm, row.target
        writer.writerow(
            [
                code_system.title,
                source.user_key,
                source.name,
                adm.user_key if adm else "",
                adm.name if adm else "",
                "8S" if target else "",
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
