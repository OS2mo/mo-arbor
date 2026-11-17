# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import json
from typing import cast
from uuid import UUID

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from mo_arbor.code_system_file import Rows
from mo_arbor.config import CodeSystem
from mo_arbor.config import CodeSystemName
from mo_arbor.config import Settings
from mo_arbor.sor import SorRows
from tests.helpers import file
from tests.helpers import row


@pytest.mark.parametrize("name,rows_model", [("sor", SorRows), ("okosted", Rows)])
def test_rows_model_by_name(name: CodeSystemName, rows_model: type[Rows]) -> None:
    assert CodeSystem(name=name).rows_model is rows_model


@pytest.mark.parametrize("name,title", [("sor", "SOR"), ("okosted", "Økosted")])
def test_title(name: CodeSystemName, title: str) -> None:
    assert CodeSystem(name=name).title == title


def test_parent() -> None:
    """Økosted's roots go under its root unit, and SOR's are at the top."""
    sor = CodeSystem(name="sor")
    okosted = CodeSystem(name="okosted")
    units = Rows.parse(file(row("R"), row("C", parent="R")))
    assert okosted.root_unit is not None
    assert okosted.parent_uuid(units["R"]) == okosted.root_unit.uuid
    assert okosted.parent_uuid(units["C"]) == okosted.org_unit_uuid("R")
    assert sor.parent_uuid(units["R"]) is None


def test_unit_name() -> None:
    """SOR's root is called SOR, and Økosted's roots keep their names."""
    sor = CodeSystem(name="sor")
    okosted = CodeSystem(name="okosted")
    units = Rows.parse(file(row("R", name="Region"), row("C", parent="R", name="Afd")))
    assert sor.unit_name(units["R"]) == "SOR"
    assert sor.unit_name(units["C"]) == "Afd"
    assert okosted.unit_name(units["R"]) == "Region"


def test_okosted_top_is_its_root_unit() -> None:
    """Økosted's roots, its legal entities, go under its root unit."""
    okosted = CodeSystem(name="okosted")
    units = Rows.parse(file(row("A"), row("B"), row("C", parent="A")))
    assert okosted.root_unit is not None
    assert okosted.top_uuids(units) == [okosted.root_unit.uuid]


def test_sor_top_is_its_root() -> None:
    """SOR has no root unit, so its dump's root is at the top."""
    sor = CodeSystem(name="sor")
    units = Rows.parse(file(row("R"), row("C", parent="R")))
    assert sor.top_uuids(units) == [sor.org_unit_uuid("R")]


def test_unknown_code_system() -> None:
    """A misspelt name must not skip the validation of its codes."""
    with pytest.raises(ValidationError) as exc_info:
        CodeSystem.parse_obj({"name": "sr"})
    assert [e["loc"] for e in exc_info.value.errors()] == [("name",)]


def test_rows_model_of_unvalidated_name() -> None:
    """A name that skipped validation fails instead of returning None."""
    name = cast(CodeSystemName, "sr")
    code_system = CodeSystem.construct(name=name)
    with pytest.raises(AssertionError):
        code_system.rows_model  # noqa: B018


@pytest.mark.usefixtures("minimal_valid_environmental_variables")
def test_code_systems(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CODE_SYSTEMS", json.dumps(["sor", "okosted"]))
    assert Settings().code_systems == {"sor", "okosted"}


@pytest.mark.usefixtures("minimal_valid_environmental_variables")
def test_unknown_code_system_name(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CODE_SYSTEMS", json.dumps(["sr"]))
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert [e["loc"] for e in exc_info.value.errors()] == [("code_systems", 0)]


def test_uuids_do_not_change() -> None:
    """Only this test notices if the way UUIDs are derived changes.

    The other tests get their UUIDs from org_unit_uuid(). A change would make
    MO's existing units unreachable.
    """
    sor = CodeSystem(name="sor")
    assert sor.org_unit_uuid("1001000016005") == UUID(
        "bc2ac4b5-32c4-530c-b504-287e326fbe52"
    )
