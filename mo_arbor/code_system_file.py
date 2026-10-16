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
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Sequence
from datetime import date
from typing import Any

from more_itertools import duplicates_everseen
from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import ValidationError
from pydantic import root_validator
from pydantic import validator


class InvalidFile(Exception):
    pass


class Row(BaseModel, frozen=True, anystr_strip_whitespace=True, extra=Extra.forbid):
    """A row in a code system file.

    Every column is read, so a file with other columns is rejected. A code gone
    from the file is terminated.
    """

    user_key: str = Field(alias="kode", min_length=1)
    # Empty for a root
    parent_user_key: str | None = Field(..., alias="kode_parent")
    validity_from: date = Field(alias="gyldig_fra")
    # The last valid day, empty if open-ended
    validity_to: date | None = Field(..., alias="gyldig_til")
    name: str = Field(alias="navn", min_length=1)
    org_unit_type: str = Field(alias="type", min_length=1)
    org_unit_level: str = Field(alias="niveau", min_length=1)
    # Not used
    active: str = Field(alias="aktiv")
    deleted: str = Field(alias="dw_is_deleted")
    inserted: str = Field(alias="dw_timestamp_insert")
    updated: str = Field(alias="dw_timestamp_update")

    @validator("parent_user_key", "validity_to", pre=True)
    def empty_is_none(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @validator("validity_to")
    def not_before_validity_from(cls, v: date | None, values: dict) -> date | None:
        validity_from = values.get("validity_from")
        if v is not None and validity_from is not None and v < validity_from:
            raise ValueError("before gyldig_fra")
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


class TopUnit(BaseModel, frozen=True):
    """A unit above the roots of a file, for code systems with several roots.

    It is valid from the earliest root's start, and open-ended, so no root is
    clamped to it.
    """

    user_key: str
    name: str
    org_unit_type: str
    org_unit_level: str


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
        validity_to=row.validity_to,
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

    def to_units(self, top_unit: TopUnit | None = None) -> dict[str, Unit]:
        children = _children(self.__root__)
        roots = children[None]
        units: dict[str, Unit] = {}
        top = None
        if top_unit is not None:
            top = Unit(
                **top_unit.dict(),
                parent=None,
                validity_from=min(root.validity_from for root in roots),
                validity_to=None,
            )
            units[top.user_key] = top
        for root in roots:
            units |= _units(root, top, children)
        return units


def parse(
    text: str,
    is_valid_code: Callable[[str], bool] | None = None,
    top_unit: TopUnit | None = None,
) -> dict[str, Unit]:
    """Parse and validate a code system file.

    The rows without a parent are roots, which become the code system's top
    units in MO, or the children of `top_unit`.

    Args:
        text: The file.
        is_valid_code: Checks the codes, for code systems whose codes have a
            known form, such as `is_sor_id`.
        top_unit: A unit to put above the roots, for code systems with
            several roots.

    Returns:
        The units, keyed by user_key.

    Raises:
        InvalidFile: If the file fails validation.
    """
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";")
    # The reader keeps the last of two columns with the same name. The header
    # is None for an empty file, which then fails as having no root.
    duplicates = list(duplicates_everseen(reader.fieldnames or []))
    if duplicates:
        raise InvalidFile(f"duplicate columns: {duplicates}")
    try:
        rows = Rows.parse_obj(list(reader))
        units = rows.to_units(top_unit)
    except ValidationError as e:
        raise InvalidFile(str(e)) from None
    codes = [row.user_key for row in rows.__root__]
    if top_unit is not None and top_unit.user_key in codes:
        raise InvalidFile(f"the top unit's code is in the file: {top_unit.user_key}")
    if is_valid_code is not None:
        # Every parent is a row, so this checks the parents' codes too
        invalid = sorted(c for c in codes if not is_valid_code(c))
        if invalid:
            raise InvalidFile(f"invalid codes: {invalid}")
    return units
