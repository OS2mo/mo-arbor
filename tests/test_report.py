# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections import defaultdict
from datetime import date
from datetime import datetime
from uuid import UUID
from uuid import uuid4

import pytest
from pytest import MonkeyPatch

from mo_arbor.config import CodeSystem
from mo_arbor.config import ReportSettings
from mo_arbor.config import Settings
from mo_arbor.dumps import DumpStore
from mo_arbor.report import Chain
from mo_arbor.report import Period
from mo_arbor.report import ReportUnit
from mo_arbor.report import Systems
from mo_arbor.report import UnitHistory
from mo_arbor.report import UnitPeriod
from mo_arbor.report import chains
from mo_arbor.report import merged
from mo_arbor.report import report_file_name
from mo_arbor.report import to_csv


def days(start: date, end: date | None) -> Period:
    return Period(start=start, end=end)


def unit(user_key: str, name: str = "Unit") -> ReportUnit:
    return ReportUnit(uuid=uuid4(), user_key=user_key, name=name)


def related(*pairs: tuple[ReportUnit, ReportUnit]) -> dict[UUID, set[UUID]]:
    by_uuid: defaultdict[UUID, set[UUID]] = defaultdict(set)
    for a, b in pairs:
        by_uuid[a.uuid].add(b.uuid)
        by_uuid[b.uuid].add(a.uuid)
    # A plain dict, as chains gets outside the tests, so a lookup of a unit
    # without relations fails here too
    return dict(by_uuid)


@pytest.mark.parametrize(
    "periods,expected",
    [
        # A relation removed on the day it was made has no days
        ([days(date(2025, 1, 1), date(2025, 1, 1))], []),
        # Split where the unit's other relations were set
        (
            [days(date(2024, 1, 1), None), days(date(2020, 1, 1), date(2024, 1, 1))],
            [days(date(2020, 1, 1), None)],
        ),
        (
            [
                days(date(2020, 1, 1), date(2023, 1, 1)),
                days(date(2022, 1, 1), date(2024, 1, 1)),
            ],
            [days(date(2020, 1, 1), date(2024, 1, 1))],
        ),
        # Removed, and made again later
        (
            [
                days(date(2020, 1, 1), date(2021, 1, 1)),
                days(date(2022, 1, 1), None),
            ],
            [
                days(date(2020, 1, 1), date(2021, 1, 1)),
                days(date(2022, 1, 1), None),
            ],
        ),
    ],
)
def test_merged(periods: list[Period], expected: list[Period]) -> None:
    assert merged(periods) == expected


def test_unit_at() -> None:
    """As it was on the day, or None if it was not active."""
    history = UnitHistory(
        uuid=uuid4(),
        periods=(
            UnitPeriod(
                start=date(2020, 1, 1),
                end=date(2021, 1, 1),
                user_key="A",
                name="Gammel",
            ),
            UnitPeriod(start=date(2022, 1, 1), end=None, user_key="A", name="Ny"),
        ),
    )

    assert history.at(date(2020, 12, 31)) == ReportUnit(
        uuid=history.uuid, user_key="A", name="Gammel"
    )
    # The end is not part of a period
    assert history.at(date(2021, 1, 1)) is None
    assert history.at(date(2022, 1, 1)) == ReportUnit(
        uuid=history.uuid, user_key="A", name="Ny"
    )


@pytest.mark.parametrize(
    "end,empty",
    [(None, False), (date(2020, 1, 2), False), (date(2020, 1, 1), True)],
)
def test_period_empty(end: date | None, empty: bool) -> None:
    assert Period(start=date(2020, 1, 1), end=end).empty is empty


def test_chains() -> None:
    """A row per chain, which may stop after its source or Adm unit."""
    # B is related to two Adm units, one of which is related to two target units
    a, b, c = unit("A"), unit("B"), unit("C")
    adm1, adm2 = unit("ADM1"), unit("ADM2")
    s1, s2 = unit("S1"), unit("S2")
    # Related to C, but in neither tree
    other = unit("OTHER")

    rows = chains(
        sources=[c, b, a],
        adm_units={u.uuid: u for u in [adm1, adm2]},
        target_units={u.uuid: u for u in [s1, s2]},
        related=related(
            (b, adm2), (b, adm1), (adm1, s2), (adm1, s1), (c, other), (c, s1)
        ),
    )

    assert rows == [
        Chain(source=a, adm=None, target=None),
        Chain(source=b, adm=adm1, target=s1),
        Chain(source=b, adm=adm1, target=s2),
        Chain(source=b, adm=adm2, target=None),
        # Only through an Adm unit
        Chain(source=c, adm=None, target=None),
    ]


def test_csv() -> None:
    """Every field quoted, `"` doubled, `;` separated, CRLF and no BOM."""
    rows = [
        Chain(
            source=unit("1", 'Afd; "Syd"'),
            adm=unit("ADM", "Æble, ø"),
            target=unit("S", "Target-enhed"),
        ),
        Chain(source=unit("2", "Uden"), adm=None, target=None),
    ]

    assert (
        to_csv(Systems(source="Økosted", adm="Adm-træet", target="Target-træet"), rows)
        == (
            '"Source_System";"Source_Code";"Source_Name";"Adm_System";"Adm_Code";'
            '"Adm_Name";"Target_System";"Target_Code";"Target_Name"\r\n'
            '"Økosted";"1";"Afd; ""Syd""";"Adm-træet";"ADM";"Æble, ø";"Target-træet";"S";'
            '"Target-enhed"\r\n'
            '"Økosted";"2";"Uden";"";"";"";"";"";""\r\n'
        ).encode()
    )


@pytest.mark.parametrize("name", ["sor", "okosted"])
def test_report_is_not_a_dump(name: str) -> None:
    code_system = CodeSystem.parse_obj({"name": name})
    file_name = report_file_name(code_system, datetime(2026, 11, 17, 12, 0, 0))
    assert file_name == f"{name}_relations_20261117_120000.csv"
    assert DumpStore(name).dump_time(file_name) is None


@pytest.mark.usefixtures("minimal_valid_environmental_variables")
def test_report_settings(monkeypatch: MonkeyPatch) -> None:
    root_adm, root_target = uuid4(), uuid4()
    monkeypatch.setenv("CODE_SYSTEMS", '["sor"]')
    assert Settings().report is None

    monkeypatch.setenv("REPORT__ROOT_ADM", str(root_adm))
    monkeypatch.setenv("REPORT__ROOT_TARGET", str(root_target))
    assert Settings().report == ReportSettings(
        root_adm=root_adm, root_target=root_target
    )
