# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
"""Parsing and validation of code system files.

The format is described in the supplier's spec "Kodesystemfiler til OS2mo",
see https://redmine.magenta.dk/issues/69230.

A file that fails validation is rejected as a whole.
"""

import csv
import io
from datetime import date
from graphlib import CycleError
from graphlib import TopologicalSorter
from typing import Any

from more_itertools import duplicates_everseen
from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError
from pydantic import root_validator
from pydantic import validator


class InvalidFile(Exception):
    pass


class Row(BaseModel, frozen=True, anystr_strip_whitespace=True):
    """A row in a code system file.

    Other columns, such as aktiv, dw_is_deleted and the timestamps, are
    ignored. A unit gone from the file is terminated.
    """

    user_key: str = Field(alias="kode", min_length=1)
    # Empty for a root
    parent_user_key: str | None = Field(..., alias="kode_parent")
    validity_from: date = Field(alias="gyldig_fra")
    # The last valid day, empty if open-ended
    validity_to: date | None = Field(..., alias="gyldig_til")
    name: str = Field(alias="navn", min_length=1)
    # The user_keys of classes in MO's org_unit_type and org_unit_level facets,
    # which the event handler looks up
    org_unit_type: str = Field(alias="type", min_length=1)
    org_unit_level: str = Field(alias="niveau", min_length=1)

    @validator("parent_user_key", "validity_to", pre=True)
    def empty_is_none(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @validator("validity_to")
    def not_before_validity_from(cls, v: date | None, values: dict) -> date | None:
        # Not in values if validity_from failed validation
        validity_from = values.get("validity_from")
        if v is not None and validity_from is not None and v < validity_from:
            raise ValueError("before gyldig_fra")
        return v


# By default, pydantic copies a model given as a field value, such as
# `parent`. copy_on_model_validation="none" stops that, so a unit's parent is
# the parent's unit itself, not a copy of it and of every unit above it.
class Unit(BaseModel, frozen=True, copy_on_model_validation="none"):
    """A unit as it should be in MO.

    The values computed from the parent are properties rather than
    cached_property, which pydantic would put in `dict()` and `==`.
    """

    user_key: str
    parent: "Unit | None"
    name: str
    org_unit_type: str
    org_unit_level: str
    validity_from: date
    # The last valid day, None if open-ended
    validity_to: date | None

    @property
    def parent_user_key(self) -> str | None:
        return None if self.parent is None else self.parent.user_key

    @property
    def depth(self) -> int:
        """Distance from its root, which has depth 1."""
        return 1 if self.parent is None else self.parent.depth + 1

    # start and end are clamped to the parent's, as MO rejects a unit that is
    # valid outside its parent's validity.
    @property
    def start(self) -> date:
        if self.parent is None:
            return self.validity_from
        return max(self.validity_from, self.parent.start)

    @property
    def end(self) -> date | None:
        """The last valid day, None if open-ended."""
        if self.parent is None or self.parent.end is None:
            return self.validity_to
        if self.validity_to is None:
            return self.parent.end
        return min(self.validity_to, self.parent.end)

    @root_validator(skip_on_failure=True)
    def valid_while_parent_is(cls, values: dict[str, Any]) -> dict[str, Any]:
        unit = cls.construct(**values)
        if unit.end is not None and unit.end < unit.start:
            raise ValueError(f"{unit.user_key}: not valid while its parent is")
        return values


class Rows(BaseModel):
    """The rows of a file, as trees under one or more roots.

    Each check assumes the ones before it passed, so it has `skip_on_failure`:
    it is skipped once a check before it, or a row, has failed. Without it,
    every check would run and could fail on what an earlier one rejected.
    """

    __root__: tuple[Row, ...]

    @root_validator(skip_on_failure=True)
    def has_rows(cls, values: dict[str, Any]) -> dict[str, Any]:
        if len(values["__root__"]) == 0:
            raise ValueError("no rows")
        return values

    @root_validator(skip_on_failure=True)
    def unique_user_keys(cls, values: dict[str, Any]) -> dict[str, Any]:
        rows = values["__root__"]
        duplicates = set(duplicates_everseen(r.user_key for r in rows))
        if duplicates:
            raise ValueError(f"duplicate kode: {', '.join(sorted(duplicates))}")
        return values

    @root_validator(skip_on_failure=True)
    def has_root(cls, values: dict[str, Any]) -> dict[str, Any]:
        rows = values["__root__"]
        if not any(r.parent_user_key is None for r in rows):
            raise ValueError("no root, a row without kode_parent")
        return values

    @root_validator(skip_on_failure=True)
    def known_parents(cls, values: dict[str, Any]) -> dict[str, Any]:
        rows = values["__root__"]
        user_keys = {r.user_key for r in rows}
        parents = {r.parent_user_key for r in rows if r.parent_user_key is not None}
        unknown = parents - user_keys
        if unknown:
            raise ValueError(f"unknown kode_parent: {', '.join(sorted(unknown))}")
        return values

    @root_validator(skip_on_failure=True)
    def no_cycles(cls, values: dict[str, Any]) -> dict[str, Any]:
        rows = values["__root__"]
        # Every parent is known, so a row is under a root unless it is in a
        # cycle, or under one
        graph = {r.user_key: [r.parent_user_key] for r in rows}
        try:
            TopologicalSorter(graph).prepare()
        except CycleError as e:
            raise ValueError(f"cycle: {e.args[1]}") from e
        return values

    def to_units(self) -> dict[str, Unit]:
        rows = {r.user_key: r for r in self.__root__}
        graph = {key: [r.parent_user_key] for key, r in rows.items()}
        units: dict[str, Unit] = {}
        # Each parent before its children, so its unit exists
        for key in TopologicalSorter(graph).static_order():
            if key is None:
                # The roots' parent
                continue
            row = rows[key]
            parent = row.parent_user_key
            units[key] = Unit(
                user_key=row.user_key,
                parent=None if parent is None else units[parent],
                name=row.name,
                org_unit_type=row.org_unit_type,
                org_unit_level=row.org_unit_level,
                validity_from=row.validity_from,
                validity_to=row.validity_to,
            )
        return units

    @classmethod
    def parse(cls, text: str) -> dict[str, Unit]:
        """Parse and validate a code system file.

        The rows without a parent are roots, which become the code system's top
        units in MO.

        Args:
            text: The file.

        Returns:
            The units in the file, keyed by user_key.

        Raises:
            InvalidFile: If the file fails validation.
        """
        reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";")
        try:
            return cls.parse_obj(list(reader)).to_units()
        except ValidationError as e:
            raise InvalidFile(str(e)) from e
