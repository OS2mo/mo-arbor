# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from typing import Literal
from typing import assert_never
from uuid import NAMESPACE_URL
from uuid import UUID
from uuid import uuid5

from fastramqpi.config import Settings as FastRAMQPISettings
from pydantic import BaseModel
from pydantic import BaseSettings

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
    # events in MO, the end of its dumps' file names, and part of its units'
    # UUIDs, so renaming a code system makes MO's existing units unreachable.
    name: CodeSystemName

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

    @property
    def root_name(self) -> str | None:
        """The name in MO of the dumps' root, or None to keep the dumps' names.

        SOR's dumps have a single root, which is called SOR in MO, whatever the
        supplier names it. Økosted's roots are its legal entities, which keep
        their names under the Økosted root unit.
        """
        match self.name:
            case "sor":
                return "SOR"
            case "okosted":
                return None
            case _:  # pragma: no cover
                assert_never(self.name)

    @property
    def title(self) -> str:
        """The code system's title in the report, e.g. "Økosted" for okosted."""
        match self.name:
            case "sor":
                return "SOR"
            case "okosted":
                return "Økosted"
            case _:  # pragma: no cover
                assert_never(self.name)

    def unit_name(self, unit: Unit) -> str:
        """The name of a unit in MO."""
        if unit.parent is None and self.root_name is not None:
            return self.root_name
        return unit.name

    def top_uuids(self, units: dict[str, Unit]) -> list[UUID]:
        """The UUIDs in MO of the units at the top of the code system's tree.

        That is its root unit, or a dump's roots if it has none.
        """
        if self.root_unit is not None:
            return [self.root_unit.uuid]
        return [
            self.org_unit_uuid(user_key)
            for user_key, unit in units.items()
            if unit.parent is None
        ]

    def org_unit_uuid(self, user_key: str) -> UUID:
        namespace = uuid5(NAMESPACE_URL, self.name)
        return uuid5(namespace, user_key)

    def parent_uuid(self, unit: Unit) -> UUID | None:
        """The UUID of a unit's parent in MO."""
        if unit.parent_user_key is not None:
            return self.org_unit_uuid(unit.parent_user_key)
        if self.root_unit is None:
            return None
        return self.root_unit.uuid


class ReportSettings(BaseModel, frozen=True):
    """The roots in MO of the trees the report links the code systems to."""

    # The administrative units, which the code systems' units are related to
    root_adm: UUID
    # 8S's units, which the administrative units are related to
    root_8s: UUID


class Settings(BaseSettings):
    class Config:
        frozen = True
        env_nested_delimiter = "__"

    fastramqpi: FastRAMQPISettings

    # The code systems to ingest, as a JSON list of names, e.g.
    # CODE_SYSTEMS='["sor", "okosted"]'.
    code_systems: set[CodeSystemName]

    # Refuse to ingest a dump that removes more units than this, unless forced.
    # Protects against a truncated dump terminating half the tree.
    max_terminations: int = 10

    # The report of the code systems' links to 8S, e.g.
    # REPORT__ROOT_ADM=<uuid> and REPORT__ROOT_8S=<uuid>. None to not report.
    report: ReportSettings | None = None
