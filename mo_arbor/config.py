# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from typing import Literal
from typing import assert_never
from uuid import NAMESPACE_URL
from uuid import UUID
from uuid import uuid5

from fastramqpi.config import Settings as FastRAMQPISettings
from more_itertools import duplicates_everseen
from pydantic import BaseModel
from pydantic import BaseSettings
from pydantic import Field
from pydantic import validator

from mo_arbor.code_system_file import Rows
from mo_arbor.code_system_file import Unit
from mo_arbor.sor import SorRows

CodeSystemName = Literal["sor", "okosted"]


class RootUnit(BaseModel, frozen=True):
    """A unit the integration makes in MO, which a code system's roots go under."""

    # Not derived from its user_key like the other units', so changing its
    # user_key does not make a new root unit
    uuid: UUID
    user_key: str
    name: str
    org_unit_type_user_key: str
    # Before every unit of the code system, as MO rejects a unit that is valid
    # before its parent
    validity_from: date


class CodeSystem(BaseModel, frozen=True):
    """A code system, such as SOR, whose dumps become a tree of org units."""

    # Which code system it is. It is also the namespace of the code system's
    # events in MO, and part of its units' UUIDs, so renaming a code system
    # makes MO's existing units unreachable.
    name: CodeSystemName

    # File names of the code system's dumps in MO's EXPORTS file store, with
    # the time of the dump as `datetime.strptime` directives, e.g.
    # customer_system_%Y%m%d_%H%M%S.csv.
    file_pattern: str = Field(min_length=1)

    # The UUID of a unit made by hand in MO, which the dumps' roots are put
    # under, for code systems whose dumps have several roots, such as Økosted.
    # Without it, the roots are at the top of MO.
    root: UUID | None = None

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
            case _:
                assert_never(self.name)

    @property
    def root_unit(self) -> RootUnit | None:
        """The unit the dumps' roots go under, or None if they are at the top.

        Økosted's dumps have several roots, its legal entities, which belong
        under one Økosted unit.
        """
        match self.name:
            case "sor":
                return None
            case "okosted":
                return RootUnit(
                    uuid=uuid5(NAMESPACE_URL, "Økosted"),
                    user_key="okosted",
                    name="Økosted",
                    org_unit_type_user_key="region",
                    validity_from=date(1900, 1, 1),
                )
            case _:  # pragma: no cover
                assert_never(self.name)

    def org_unit_uuid(self, user_key: str) -> UUID:
        namespace = uuid5(NAMESPACE_URL, self.name)
        return uuid5(namespace, user_key)

    def parent_uuid(self, unit: Unit) -> UUID | None:
        """The UUID of a unit's parent in MO."""
        if unit.parent_user_key is None:
            return self.root
        return self.org_unit_uuid(unit.parent_user_key)


class Settings(BaseSettings):
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

    def get_code_system(self, name: str) -> CodeSystem | None:
        """The code system with this name, or None if it is not configured."""
        for c in self.code_systems:
            if c.name == name:
                return c
        return None
