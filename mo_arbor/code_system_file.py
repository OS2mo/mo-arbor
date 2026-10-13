# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
"""Parsing and validation of code system files.

The format is described in the supplier's spec "Kodesystemfiler til OS2mo",
see https://redmine.magenta.dk/issues/69230. A file that fails validation is
rejected as a whole.
"""

import csv
import io
from collections import defaultdict
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Sequence
from datetime import date
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

    Other columns, such as gyldig_til, aktiv, dw_is_deleted and the
    timestamps, are ignored: a code in the file is active, and a code gone
    from it is terminated.
    """

    user_key: str = Field(alias="kode", min_length=1)
    # Empty for a root
    parent_user_key: str | None = Field(..., alias="kode_parent")
    validity_from: date = Field(alias="gyldig_fra")
    name: str = Field(alias="navn", min_length=1)
    org_unit_type: str = Field(alias="type", min_length=1)
    org_unit_level: str = Field(alias="niveau", min_length=1)

    @validator("parent_user_key", pre=True)
    def empty_is_none(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v


# The parent is kept as it is, not copied, as every unit under it refers to it
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

    @property
    def parent_user_key(self) -> str | None:
        return None if self.parent is None else self.parent.user_key

    @property
    def depth(self) -> int:
        """Distance from its root, which has depth 1."""
        return 1 if self.parent is None else self.parent.depth + 1

    # start is clamped to the parent's, as MO rejects a unit that starts
    # before its parent.
    @property
    def start(self) -> date:
        if self.parent is None:
            return self.validity_from
        return max(self.validity_from, self.parent.start)


def _user_keys(rows: Iterable[Row]) -> str:
    return ", ".join(sorted({row.user_key for row in rows}))


def _children(rows: list[Row]) -> defaultdict[str | None, list[Row]]:
    """The rows under each user_key, and the roots under None."""
    children: defaultdict[str | None, list[Row]] = defaultdict(list)
    for row in rows:
        children[row.parent_user_key].append(row)
    return children


def _user_keys_under(
    user_key: str, children: Mapping[str | None, Sequence[Row]]
) -> set[str]:
    """The user_key and every user_key under it."""
    user_keys = {user_key}
    for child in children[user_key]:
        user_keys |= _user_keys_under(child.user_key, children)
    return user_keys


def _units(
    row: Row, parent: Unit | None, children: Mapping[str | None, Sequence[Row]]
) -> dict[str, Unit]:
    """The unit of a row, and the units under it."""
    unit = Unit(
        user_key=row.user_key,
        parent=parent,
        name=row.name,
        org_unit_type=row.org_unit_type,
        org_unit_level=row.org_unit_level,
        validity_from=row.validity_from,
    )
    units = {row.user_key: unit}
    for child in children[row.user_key]:
        units |= _units(child, unit, children)
    return units


class Rows(BaseModel):
    """The rows of a file, as trees under one or more roots.

    Each check assumes the ones before it passed, so they stop at the first
    that fails.
    """

    __root__: list[Row]

    @root_validator(skip_on_failure=True)
    def unique_user_keys(cls, values: dict[str, Any]) -> dict[str, Any]:
        rows = values["__root__"]
        duplicates = list(duplicates_everseen(rows, key=lambda r: r.user_key))
        if duplicates:
            raise ValueError(f"duplicate kode: {_user_keys(duplicates)}")
        return values

    @root_validator(skip_on_failure=True)
    def has_root(cls, values: dict[str, Any]) -> dict[str, Any]:
        if all(r.parent_user_key is not None for r in values["__root__"]):
            raise ValueError("no root, a row without kode_parent")
        return values

    @root_validator(skip_on_failure=True)
    def known_parents(cls, values: dict[str, Any]) -> dict[str, Any]:
        rows = values["__root__"]
        user_keys = {r.user_key for r in rows}
        unknown = [
            r
            for r in rows
            if r.parent_user_key is not None and r.parent_user_key not in user_keys
        ]
        if unknown:
            raise ValueError(f"unknown kode_parent in: {_user_keys(unknown)}")
        return values

    @root_validator(skip_on_failure=True)
    def all_under_roots(cls, values: dict[str, Any]) -> dict[str, Any]:
        rows = values["__root__"]
        children = _children(rows)
        under_roots: set[str] = set()
        for root in children[None]:
            under_roots |= _user_keys_under(root.user_key, children)
        # Every parent is known, so a row not under a root is in a cycle, or
        # under one
        cycles = [r for r in rows if r.user_key not in under_roots]
        if cycles:
            raise ValueError(f"not under a root: {_user_keys(cycles)}")
        return values

    def to_units(self) -> dict[str, Unit]:
        children = _children(self.__root__)
        units: dict[str, Unit] = {}
        for root in children[None]:
            units |= _units(root, None, children)
        return units


def parse(text: str) -> dict[str, Unit]:
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
        return Rows.parse_obj(list(reader)).to_units()
    except ValidationError as e:
        raise InvalidFile(str(e)) from None
