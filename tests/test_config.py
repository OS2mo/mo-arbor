# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
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

SOR = CodeSystem(name="sor", file_pattern="", uuid_namespace="sor.dk")


@pytest.mark.parametrize("name,rows_model", [("sor", SorRows), ("okosted", Rows)])
def test_rows_model_by_name(name: CodeSystemName, rows_model: type[Rows]) -> None:
    code_system = CodeSystem(name=name, file_pattern="", uuid_namespace=name)
    assert code_system.rows_model is rows_model


def test_parent() -> None:
    """The roots are put under the root, if the code system has one."""
    root = UUID("4f3a9c2e-1b7d-4e8a-9f60-2c5d8b1a7e43")
    okosted = CodeSystem(
        name="okosted", file_pattern="", uuid_namespace="okosted", root=root
    )
    units = Rows.parse(file(row("R"), row("C", parent="R")))
    assert okosted.parent(units["R"]) == root
    assert okosted.parent(units["C"]) == okosted.uuid("R")
    assert SOR.parent(units["R"]) is None


def test_unknown_code_system() -> None:
    """A misspelt name must not skip the validation of its codes."""
    with pytest.raises(ValidationError):
        CodeSystem.parse_obj({"name": "sr", "file_pattern": "", "uuid_namespace": "sr"})


def test_code_system_names_are_unique() -> None:
    """The name is the code system's event namespace."""
    okosted = CodeSystem(name="okosted", file_pattern="", uuid_namespace="okosted")
    with pytest.raises(ValidationError) as exc_info:
        _Settings(code_systems=[SOR, okosted, SOR])
    assert "duplicate code systems: sor" in str(exc_info.value)


def test_sor_uuids_match_the_importer() -> None:
    """UUIDs are derived like in the one-off importer, which created the units.

    Changing how they are derived would make MO's existing units unreachable.
    """
    assert SOR.uuid("1001000016005") == UUID("6a1ff8b2-63c5-57f6-a4e2-82a442030303")


def test_code_systems_have_their_own_uuids() -> None:
    okosted = CodeSystem(name="okosted", file_pattern="", uuid_namespace="okosted")
    assert SOR.uuid("1") != okosted.uuid("1")
