# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections.abc import Callable

import pytest
from pydantic import ValidationError

from mo_arbor.config import CodeSystem
from mo_arbor.config import CodeSystemName
from mo_arbor.config import _Settings
from mo_arbor.sor import is_sor_id


@pytest.mark.parametrize("name,is_valid_code", [("sor", is_sor_id), ("okosted", None)])
def test_code_check_by_name(
    name: CodeSystemName, is_valid_code: Callable[[str], bool] | None
) -> None:
    assert CodeSystem(name=name, file_pattern="").is_valid_code is is_valid_code


def test_top_unit() -> None:
    code_system = CodeSystem.parse_obj(
        {
            "name": "okosted",
            "file_pattern": "",
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
        CodeSystem.parse_obj({"name": "sr", "file_pattern": ""})


def test_code_system_names_are_unique() -> None:
    """The name is the code system's event namespace."""
    sor = CodeSystem(name="sor", file_pattern="")
    okosted = CodeSystem(name="okosted", file_pattern="")
    with pytest.raises(ValidationError) as exc_info:
        _Settings(code_systems=[sor, okosted, sor])
    assert "duplicate code systems: ['sor']" in str(exc_info.value)
