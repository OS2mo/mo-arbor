# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections.abc import Callable
from uuid import UUID

import pytest
from pydantic import ValidationError

from mo_arbor.config import CodeSystem
from mo_arbor.config import CodeSystemName
from mo_arbor.config import _Settings
from mo_arbor.sor import is_sor_id

SOR = CodeSystem(name="sor", file_pattern="", uuid_namespace="sor.dk")


@pytest.mark.parametrize("name,is_valid_code", [("sor", is_sor_id), ("okosted", None)])
def test_code_check_by_name(
    name: CodeSystemName, is_valid_code: Callable[[str], bool] | None
) -> None:
    code_system = CodeSystem(name=name, file_pattern="", uuid_namespace=name)
    assert code_system.is_valid_code is is_valid_code


def test_top_unit() -> None:
    code_system = CodeSystem.parse_obj(
        {
            "name": "okosted",
            "file_pattern": "",
            "uuid_namespace": "okosted",
            "top_unit": {
                "user_key": "okosted",
                "name": "Økosted",
                "org_unit_type": "økosted",
                "org_unit_level": "N1",
            },
        }
    )
    assert code_system.top_unit is not None
    assert code_system.top_unit.name == "Økosted"


def test_unknown_code_system() -> None:
    """A misspelt name must not skip the validation of its codes."""
    with pytest.raises(ValidationError):
        CodeSystem.parse_obj({"name": "sr", "file_pattern": "", "uuid_namespace": "sr"})


def test_code_system_names_are_unique() -> None:
    """The name is the code system's event namespace."""
    okosted = CodeSystem(name="okosted", file_pattern="", uuid_namespace="okosted")
    with pytest.raises(ValidationError) as exc_info:
        _Settings(code_systems=[SOR, okosted, SOR])
    assert "duplicate code systems: ['sor']" in str(exc_info.value)


def test_sor_uuids_match_the_importer() -> None:
    """UUIDs are derived like in the one-off importer, which created the units.

    Changing how they are derived would make MO's existing units unreachable.
    """
    assert SOR.uuid("1001000016005") == UUID("6a1ff8b2-63c5-57f6-a4e2-82a442030303")


def test_code_systems_have_their_own_uuids() -> None:
    okosted = CodeSystem(name="okosted", file_pattern="", uuid_namespace="okosted")
    assert SOR.uuid("1") != okosted.uuid("1")
