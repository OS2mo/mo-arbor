# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections import defaultdict
from datetime import date
from datetime import datetime
from uuid import UUID
from uuid import uuid4

import pytest
from pytest import MonkeyPatch

from mo_arbor.config import LoenReportSettings
from mo_arbor.config import Settings
from mo_arbor.dumps import DumpStore
from mo_arbor.report import Chain
from mo_arbor.report import Period
from mo_arbor.report import Related
from mo_arbor.report import Relation
from mo_arbor.report import ReportUnit
from mo_arbor.report import UnitHistory
from mo_arbor.report import UnitPeriod
from mo_arbor.report import loen_chains
from mo_arbor.report import loen_csv
from mo_arbor.report import merged
from mo_arbor.report import report_file_name

TODAY = date(2026, 11, 25)
ALWAYS = Period(start=date(2020, 1, 1), end=None)


def days(start: date, end: date | None) -> Period:
    return Period(start=start, end=end)


def unit(user_key: str, *periods: tuple[date, date | None, str]) -> UnitHistory:
    """A unit with periods of (start, end, name), active from 2020 by default."""
    periods = periods or ((ALWAYS.start, None, "Unit"),)
    return UnitHistory(
        uuid=uuid4(),
        periods=tuple(
            UnitPeriod(start=start, end=end, user_key=user_key, name=name)
            for start, end, name in periods
        ),
    )


def at(unit: UnitHistory, day: date = TODAY) -> ReportUnit:
    reported = unit.at(day)
    assert reported is not None
    return reported


def rel(unit: UnitHistory, period: Period = ALWAYS, day: date = TODAY) -> Relation:
    """The relation to the unit, named as on the day."""
    return Relation(unit=at(unit, day), period=period)


def report_unit(user_key: str, name: str = "Unit") -> ReportUnit:
    return ReportUnit(uuid=uuid4(), user_key=user_key, name=name)


def by_uuid(*units: UnitHistory) -> dict[UUID, UnitHistory]:
    return {u.uuid: u for u in units}


def related(*relations: tuple[UnitHistory, UnitHistory, Period]) -> Related:
    """The relations of (unit, unit, when)."""
    by_unit: defaultdict[UUID, list[tuple[Period, UUID]]] = defaultdict(list)
    for a, b, when in relations:
        by_unit[a.uuid].append((when, b.uuid))
        by_unit[b.uuid].append((when, a.uuid))
    # A plain dict, as the report gets outside the tests, so a lookup of a unit
    # without relations fails here too
    return dict(by_unit)


@pytest.mark.parametrize(
    "periods,day",
    [
        # Active today
        ([(date(2020, 1, 1), None)], TODAY),
        # Ended, on its last day
        ([(date(2020, 1, 1), date(2021, 1, 1))], date(2020, 12, 31)),
        # The last day of its last period
        (
            [
                (date(2020, 1, 1), date(2021, 1, 1)),
                (date(2021, 1, 1), date(2022, 1, 1)),
            ],
            date(2021, 12, 31),
        ),
        # Not started, on its first day
        ([(date(2027, 1, 1), None)], date(2027, 1, 1)),
        # Ended, but opens again later
        (
            [(date(2020, 1, 1), date(2021, 1, 1)), (date(2027, 1, 1), None)],
            date(2027, 1, 1),
        ),
    ],
)
def test_report_day(periods: list[tuple[date, date | None]], day: date) -> None:
    history = unit("A", *((start, end, "A") for start, end in periods))
    assert history.report_day(TODAY) == day


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


def test_loen_chains() -> None:
    """A row per chain, which may stop after its source or Adm unit."""
    # B is related to two Adm units, one of which is related to two løn units
    a, b, c = unit("A"), unit("B"), unit("C")
    adm1, adm2 = unit("ADM1"), unit("ADM2")
    s1, s2 = unit("S1"), unit("S2")
    # Related to C, but in neither tree
    other = unit("OTHER")

    rows = loen_chains(
        sources=[c, b, a],
        adm_units=by_uuid(adm1, adm2),
        loen_units=by_uuid(s1, s2),
        related=related(
            (b, adm2, ALWAYS),
            (b, adm1, ALWAYS),
            (adm1, s2, ALWAYS),
            (adm1, s1, ALWAYS),
            (c, other, ALWAYS),
            (c, s1, ALWAYS),
        ),
        today=TODAY,
    )

    assert rows == [
        Chain(source=at(a), adm=None, loen=None),
        Chain(source=at(b), adm=rel(adm1), loen=rel(s1)),
        Chain(source=at(b), adm=rel(adm1), loen=rel(s2)),
        Chain(source=at(b), adm=rel(adm2), loen=None),
        # Only through an Adm unit
        Chain(source=at(c), adm=None, loen=None),
    ]


def test_same_code() -> None:
    """In the same order, whichever order MO returns the units in."""
    a = unit("A")
    first, second = sorted([unit("ADM"), unit("ADM")], key=lambda u: u.uuid)

    for adm_units in [(first, second), (second, first)]:
        rows = loen_chains(
            sources=[a],
            adm_units=by_uuid(*adm_units),
            loen_units={},
            related=related(*((a, adm, ALWAYS) for adm in adm_units)),
            today=TODAY,
        )

        assert rows == [
            Chain(source=at(a), adm=rel(first), loen=None),
            Chain(source=at(a), adm=rel(second), loen=None),
        ]


def test_relations_over_time() -> None:
    """A row for each relation the source has had, by code, then oldest first."""
    a = unit("A")
    adm1, adm2 = unit("ADM1"), unit("ADM2")
    until_2024 = days(date(2020, 1, 1), date(2024, 1, 1))
    # Moved to ADM2 for a year, then back to ADM1
    from_2025 = days(date(2025, 1, 1), None)
    until_2025 = days(date(2024, 1, 1), date(2025, 1, 1))
    before = date(2023, 12, 31)

    rows = loen_chains(
        sources=[a],
        adm_units=by_uuid(adm1, adm2),
        loen_units={},
        related=related(
            (a, adm1, from_2025),
            (a, adm2, until_2025),
            (a, adm1, until_2024),
        ),
        today=TODAY,
    )

    assert rows == [
        Chain(source=at(a, before), adm=rel(adm1, until_2024, before), loen=None),
        Chain(source=at(a), adm=rel(adm1, from_2025), loen=None),
        Chain(
            source=at(a, date(2024, 12, 31)),
            adm=rel(adm2, until_2025, date(2024, 12, 31)),
            loen=None,
        ),
    ]


def test_loen_relation_valid_with_the_adm_relation() -> None:
    """Only while both relations of a chain were valid, with their own dates."""
    a, adm = unit("A"), unit("ADM")
    s1, s2 = unit("S1"), unit("S2")
    from_2023 = days(date(2023, 1, 1), None)
    # Ended before A was related to ADM
    s1_until_2022 = days(date(2020, 1, 1), date(2022, 1, 1))
    s2_until_2024 = days(date(2020, 1, 1), date(2024, 1, 1))
    last_day = date(2023, 12, 31)

    rows = loen_chains(
        sources=[a],
        adm_units=by_uuid(adm),
        loen_units=by_uuid(s1, s2),
        related=related(
            (a, adm, from_2023),
            (adm, s1, s1_until_2022),
            (adm, s2, s2_until_2024),
        ),
        today=TODAY,
    )

    assert rows == [
        Chain(
            source=at(a, last_day),
            adm=rel(adm, from_2023, last_day),
            loen=rel(s2, s2_until_2024, last_day),
        )
    ]


def test_named_on_the_rows_day() -> None:
    """An ended unit's row, as it was when it closed."""
    last_day = date(2023, 12, 31)
    ended = unit("ENDED", (date(2020, 1, 1), date(2024, 1, 1), "Lukket"))
    # Renamed after the unit closed, so its old name is reported
    adm = unit(
        "ADM",
        (date(2020, 1, 1), date(2025, 1, 1), "Gammel"),
        (date(2025, 1, 1), None, "Ny"),
    )
    loen = unit("S")
    # Removed from the day the unit was terminated, as MO wants
    until_2024 = days(date(2020, 1, 1), date(2024, 1, 1))

    rows = loen_chains(
        sources=[ended],
        adm_units=by_uuid(adm),
        loen_units=by_uuid(loen),
        related=related((ended, adm, until_2024), (adm, loen, ALWAYS)),
        today=TODAY,
    )

    assert rows == [
        Chain(
            source=at(ended, last_day),
            adm=Relation(
                unit=ReportUnit(uuid=adm.uuid, user_key="ADM", name="Gammel"),
                period=until_2024,
            ),
            loen=rel(loen, ALWAYS, last_day),
        )
    ]


@pytest.mark.parametrize(
    "source,day",
    [
        (
            unit("ENDED", (date(2020, 1, 1), date(2024, 1, 1), "Lukket")),
            date(2023, 12, 31),
        ),
        (unit("FUTURE", (date(2027, 1, 1), None, "Ny")), date(2027, 1, 1)),
    ],
)
def test_source_without_relations_on_its_own_day(
    source: UnitHistory, day: date
) -> None:
    rows = loen_chains(
        sources=[source], adm_units={}, loen_units={}, related={}, today=TODAY
    )

    assert rows == [Chain(source=at(source, day), adm=None, loen=None)]


def test_future_relation_on_its_first_day() -> None:
    first_day = date(2027, 1, 1)
    future = unit("FUTURE", (first_day, None, "Ny"))
    adm = unit("ADM")
    from_2027 = days(first_day, None)

    rows = loen_chains(
        sources=[future],
        adm_units=by_uuid(adm),
        loen_units={},
        related=related((future, adm, from_2027)),
        today=TODAY,
    )

    assert rows == [
        Chain(
            source=at(future, first_day), adm=rel(adm, from_2027, first_day), loen=None
        )
    ]


def test_csv() -> None:
    """Every field quoted, `"` doubled, `;` separated, CRLF and no BOM.

    To is the last day, or empty if the relation does not end.
    """
    rows = [
        Chain(
            source=report_unit("1", 'Afd; "Syd"'),
            adm=Relation(
                unit=report_unit("ADM", "Æble, ø"),
                period=days(date(2020, 1, 1), date(2024, 1, 1)),
            ),
            loen=Relation(unit=report_unit("S", "Løn-enhed"), period=ALWAYS),
        ),
        Chain(source=report_unit("2", "Uden"), adm=None, loen=None),
    ]

    assert (
        loen_csv("Adm-træet", "Løn-træet", rows)
        == (
            '"Source_System";"Source_Code";"Source_Name";"Adm_System";"Adm_Code";'
            '"Adm_Name";"Adm_From";"Adm_To";"Target_System";"Target_Code";'
            '"Target_Name";"Target_From";"Target_To"\r\n'
            '"SOR";"1";"Afd; ""Syd""";"Adm-træet";"ADM";"Æble, ø";"2020-01-01";'
            '"2023-12-31";"Løn-træet";"S";"Løn-enhed";"2020-01-01";""\r\n'
            '"SOR";"2";"Uden";"";"";"";"";"";"";"";"";"";""\r\n'
        ).encode()
    )


def test_report_is_not_a_dump() -> None:
    file_name = report_file_name("loen", datetime(2026, 11, 17, 12, 0, 0))
    assert file_name == "sor_loen_report_20261117_120000.csv"
    assert DumpStore("sor").dump_time(file_name) is None
    assert DumpStore("okosted").dump_time(file_name) is None


REPORT_ENV = {
    "LOEN_REPORT__NAME": "loen",
    "LOEN_REPORT__ROOT_ADM": str(uuid4()),
    "LOEN_REPORT__ROOT_LOEN": str(uuid4()),
}


@pytest.mark.usefixtures("minimal_valid_environmental_variables")
def test_report_settings(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CODE_SYSTEMS", '["sor"]')
    assert Settings().loen_report is None

    for key, value in REPORT_ENV.items():
        monkeypatch.setenv(key, value)
    assert Settings().loen_report == LoenReportSettings(
        name="loen",
        root_adm=UUID(REPORT_ENV["LOEN_REPORT__ROOT_ADM"]),
        root_loen=UUID(REPORT_ENV["LOEN_REPORT__ROOT_LOEN"]),
    )
