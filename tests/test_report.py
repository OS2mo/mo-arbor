# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
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
from mo_arbor.report import ReportUnit
from mo_arbor.report import chains
from mo_arbor.report import report_file_name
from mo_arbor.report import to_csv


def unit(user_key: str, name: str = "Unit") -> ReportUnit:
    return ReportUnit(uuid=uuid4(), user_key=user_key, name=name)


def related(*pairs: tuple[ReportUnit, ReportUnit]) -> dict[UUID, set[UUID]]:
    by_uuid: dict[UUID, set[UUID]] = {}
    for a, b in pairs:
        by_uuid.setdefault(a.uuid, set()).add(b.uuid)
        by_uuid.setdefault(b.uuid, set()).add(a.uuid)
    return by_uuid


def test_chains() -> None:
    """A row per chain, which may stop after its source or Adm unit."""
    # B is related to two Adm units, one of which is related to two 8S units
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
            target=unit("S", "8S-enhed"),
        ),
        Chain(source=unit("2", "Uden"), adm=None, target=None),
    ]

    assert (
        to_csv(CodeSystem(name="okosted"), rows)
        == (
            '"Source_System";"Source_Code";"Source_Name";"Adm_Code";"Adm_Name";'
            '"Target_System";"Target_Code";"Target_Name"\r\n'
            '"Økosted";"1";"Afd; ""Syd""";"ADM";"Æble, ø";"8S";"S";"8S-enhed"\r\n'
            '"Økosted";"2";"Uden";"";"";"";"";""\r\n'
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
    root_adm, root_8s = uuid4(), uuid4()
    monkeypatch.setenv("CODE_SYSTEMS", '["sor"]')
    assert Settings().report is None

    monkeypatch.setenv("REPORT__ROOT_ADM", str(root_adm))
    monkeypatch.setenv("REPORT__ROOT_8S", str(root_8s))
    assert Settings().report == ReportSettings(root_adm=root_adm, root_8s=root_8s)
