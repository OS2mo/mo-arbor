# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any

from pydantic import BaseModel

from mo_arbor.code_system_file import Unit


class Diff(BaseModel, frozen=True):
    added: set[str]
    changed: set[str]
    removed: set[str]


def _compared(unit: Unit) -> dict[str, Any]:
    """What is compared of a unit: its own fields, and what comes from its parent.

    The parent itself is left out, as comparing it would compare every unit
    above, and a renamed unit would change every unit under it.
    """
    return {
        **unit.dict(exclude={"parent"}),
        "parent_user_key": unit.parent_user_key,
        # Clamped, so they change with the parent's
        "start": unit.start,
        "end": unit.end,
    }


def diff(old: dict[str, Unit], new: dict[str, Unit]) -> Diff:
    """Find the user_keys that differ between two dumps."""
    common = old.keys() & new.keys()
    return Diff(
        added=new.keys() - old.keys(),
        changed={k for k in common if _compared(old[k]) != _compared(new[k])},
        removed=old.keys() - new.keys(),
    )
