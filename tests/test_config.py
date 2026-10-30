# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import cast
from uuid import UUID

import pytest
from pydantic import ValidationError

from mo_arbor.code_system_file import Rows
from mo_arbor.config import CodeSystem
from mo_arbor.config import CodeSystemName
from mo_arbor.config import _Settings
from mo_arbor.sor import SorRows
from tests.helpers import file
from tests.helpers import row

PATTERN = "customer_system_%Y%m%d_%H%M%S.csv"


@pytest.mark.parametrize("name,rows_model", [("sor", SorRows), ("okosted", Rows)])
def test_rows_model_by_name(name: CodeSystemName, rows_model: type[Rows]) -> None:
    assert CodeSystem(name=name, file_pattern=PATTERN).rows_model is rows_model


def test_parent() -> None:
    """The roots are put under the root, if the code system has one."""
    root = UUID("4f3a9c2e-1b7d-4e8a-9f60-2c5d8b1a7e43")
    sor = CodeSystem(name="sor", file_pattern=PATTERN)
    okosted = CodeSystem(name="okosted", file_pattern=PATTERN, root=root)
    units = Rows.parse(file(row("R"), row("C", parent="R")))
    assert okosted.parent_uuid(units["R"]) == root
    assert okosted.parent_uuid(units["C"]) == okosted.org_unit_uuid("R")
    assert sor.parent_uuid(units["R"]) is None


def test_unknown_code_system() -> None:
    """A misspelt name must not skip the validation of its codes."""
    with pytest.raises(ValidationError) as exc_info:
        CodeSystem.parse_obj({"name": "sr", "file_pattern": PATTERN})
    assert [e["loc"] for e in exc_info.value.errors()] == [("name",)]


def test_rows_model_of_unvalidated_name() -> None:
    """A name that skipped validation fails instead of returning None."""
    name = cast(CodeSystemName, "sr")
    code_system = CodeSystem.construct(name=name, file_pattern=PATTERN)
    with pytest.raises(AssertionError):
        code_system.rows_model  # noqa: B018


def test_empty_file_pattern() -> None:
    """An empty pattern matches no dump, so nothing would ever be ingested."""
    with pytest.raises(ValidationError) as exc_info:
        CodeSystem(name="sor", file_pattern="")
    assert [e["loc"] for e in exc_info.value.errors()] == [("file_pattern",)]


def test_code_system_names_are_unique() -> None:
    """The name is the code system's event namespace."""
    sor = CodeSystem(name="sor", file_pattern=PATTERN)
    okosted = CodeSystem(name="okosted", file_pattern=PATTERN)
    with pytest.raises(ValidationError) as exc_info:
        _Settings(code_systems=[sor, okosted, sor])
    assert "duplicate code systems: sor" in str(exc_info.value)


def test_uuids_do_not_change() -> None:
    """Only this test notices if the way UUIDs are derived changes.

    The other tests get their UUIDs from org_unit_uuid(). A change would make
    MO's existing units unreachable.
    """
    sor = CodeSystem(name="sor", file_pattern=PATTERN)
    assert sor.org_unit_uuid("1001000016005") == UUID(
        "bc2ac4b5-32c4-530c-b504-287e326fbe52"
    )
