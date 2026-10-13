# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections import Counter
from collections.abc import Callable
from typing import Literal
from uuid import NAMESPACE_URL
from uuid import UUID
from uuid import uuid5

from fastramqpi.config import Settings as FastRAMQPISettings
from pydantic import BaseModel
from pydantic import BaseSettings
from pydantic import validator

from mo_arbor.code_system_file import TopUnit
from mo_arbor.sor import is_sor_id

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

    # The UUID of a unit is derived from its user_key in this namespace, so
    # changing it makes MO's existing units unreachable. SOR's is "sor.dk",
    # like the one-off importer that created the units.
    uuid_namespace: str

    # Refuse to ingest a dump that removes more units than this, unless forced.
    # Protects against a truncated dump terminating half the tree.
    max_terminations: int = 10

    # A unit above the roots of the dumps, for code systems whose dumps have
    # several roots, such as Økosted. Its type and level are looked up like
    # the dumps', by user_key.
    top_unit: TopUnit | None = None

    @property
    def is_valid_code(self) -> Callable[[str], bool] | None:
        """Checks the code system's codes, if they have a known form."""
        # mypy fails if a code system is missing, so each must choose
        match self.name:
            case "sor":
                return is_sor_id
            case "okosted":
                return None

    def uuid(self, user_key: str) -> UUID:
        namespace = uuid5(NAMESPACE_URL, self.uuid_namespace)
        return uuid5(namespace, user_key)


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
        names = Counter(code_system.name for code_system in v)
        duplicates = sorted(name for name, n in names.items() if n > 1)
        if duplicates:
            raise ValueError(f"duplicate code systems: {duplicates}")
        return v
