# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Literal

from fastramqpi.config import Settings as FastRAMQPISettings
from more_itertools import duplicates_everseen
from pydantic import BaseModel
from pydantic import BaseSettings
from pydantic import validator

from mo_arbor.code_system_file import Rows
from mo_arbor.sor import SorRows

CodeSystemName = Literal["sor", "okosted"]


class CodeSystem(BaseModel, frozen=True):
    """A code system, such as SOR, whose dumps become a tree of org units."""

    # Which code system it is. It is also the namespace of the code system's
    # events in MO.
    name: CodeSystemName

    # File names of the code system's dumps in MO's EXPORTS file store, with
    # the time of the dump as `datetime.strptime` directives, e.g.
    # rsyd_sor_%Y%m%d_%H%M%S.csv.
    file_pattern: str

    # Refuse to ingest a dump that removes more units than this, unless forced.
    # Protects against a truncated dump terminating half the tree.
    max_terminations: int = 10

    @property
    def rows_model(self) -> type[Rows]:
        """The model of the code system's dumps, which checks its codes."""
        # mypy fails if a code system is missing, so each must choose
        match self.name:
            case "sor":
                return SorRows
            case "okosted":
                return Rows


class _Settings(BaseSettings):
    class Config:
        frozen = True
        env_nested_delimiter = "__"

    fastramqpi: FastRAMQPISettings

    # The code systems, as a JSON list, e.g.
    # CODE_SYSTEMS='[{"name": "sor", "file_pattern": "..."}]'.
    code_systems: list[CodeSystem]

    @validator("code_systems")
    def unique_names(cls, v: list[CodeSystem]) -> list[CodeSystem]:
        duplicates = set(duplicates_everseen(c.name for c in v))
        if duplicates:
            raise ValueError(f"duplicate code systems: {', '.join(sorted(duplicates))}")
        return v
