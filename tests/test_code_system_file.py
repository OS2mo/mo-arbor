# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from itertools import permutations

import pytest

from mo_arbor.code_system_file import InvalidFile
from mo_arbor.code_system_file import Rows
from mo_arbor.code_system_file import Unit
from tests.helpers import COLUMNS
from tests.helpers import file
from tests.helpers import row

ROOT = "R"
CHILD = "C"
GRANDCHILD = "G"


def test_parse() -> None:
    text = file(
        row(ROOT, name="Root", org_unit_type="region"),
        row(
            CHILD,
            parent=ROOT,
            name="Område",
            org_unit_level="N2",
            validity_from="2020-01-01",
        ),
        row(GRANDCHILD, parent=CHILD, name="Afdeling", org_unit_level="N3"),
    )
    units = Rows.parse(text)

    root = Unit(
        user_key=ROOT,
        parent=None,
        name="Root",
        org_unit_type="region",
        org_unit_level="N1",
        validity_from=date(2015, 7, 30),
    )
    child = Unit(
        user_key=CHILD,
        parent=root,
        name="Område",
        org_unit_type="klinisk enhed",
        org_unit_level="N2",
        validity_from=date(2020, 1, 1),
    )
    grandchild = Unit(
        user_key=GRANDCHILD,
        parent=child,
        name="Afdeling",
        org_unit_type="klinisk enhed",
        org_unit_level="N3",
        validity_from=date(2015, 7, 30),
    )
    assert units == {ROOT: root, CHILD: child, GRANDCHILD: grandchild}
    # Each unit refers to its parent's unit, not a copy
    assert units[ROOT].parent is None
    assert units[CHILD].parent is units[ROOT]
    assert units[GRANDCHILD].parent is units[CHILD]

    assert units[ROOT].parent_user_key is None
    assert units[CHILD].parent_user_key == ROOT
    assert units[GRANDCHILD].parent_user_key == CHILD

    assert units[ROOT].depth == 1
    assert units[CHILD].depth == 2
    assert units[GRANDCHILD].depth == 3


def test_aktiv_and_dw_is_deleted_are_not_used() -> None:
    text = file(
        row(
            ROOT,
            name="Root",
            org_unit_type="region",
            org_unit_level="N1",
            aktiv="false",
            dw_is_deleted="true",
        )
    )
    assert Rows.parse(text) == {
        ROOT: Unit(
            user_key=ROOT,
            parent=None,
            name="Root",
            org_unit_type="region",
            org_unit_level="N1",
            validity_from=date(2015, 7, 30),
        )
    }


def test_several_roots() -> None:
    units = Rows.parse(file(row("R1"), row("R2"), row("C", parent="R2")))
    assert units["R1"].parent is None
    assert units["R2"].parent is None
    assert units["C"].parent is units["R2"]


def test_rows_in_any_order() -> None:
    """Every order of the rows gives the same units."""
    rows = [row(ROOT), row(CHILD, parent=ROOT), row(GRANDCHILD, parent=CHILD)]
    units = Rows.parse(file(*rows))
    for order in permutations(rows):
        assert Rows.parse(file(*order)) == units


def test_values_are_stripped() -> None:
    units = Rows.parse(file(row(f" {ROOT} ", name=" Root ")))
    assert units[ROOT].user_key == ROOT
    assert units[ROOT].name == "Root"


@pytest.mark.parametrize(
    "text,error",
    [
        pytest.param("", "__root__\n  no rows", id="empty-file"),
        pytest.param(
            file(row(ROOT), columns=[c for c in COLUMNS if c != "navn"]),
            "__root__ -> 0 -> navn\n  field required",
            id="missing-column",
        ),
        pytest.param(
            # Would otherwise make every row a root
            file(row(ROOT), columns=[c for c in COLUMNS if c != "kode_parent"]),
            "__root__ -> 0 -> kode_parent\n  field required",
            id="missing-parent-column",
        ),
        pytest.param(
            file(row(ROOT), row(CHILD, parent=ROOT, org_unit_type="")),
            "__root__ -> 1 -> type\n  ensure this value has at least 1 characters",
            id="empty-type",
        ),
        pytest.param(
            file(row(ROOT), row(CHILD, parent=ROOT, org_unit_level="")),
            "__root__ -> 1 -> niveau\n  ensure this value has at least 1 characters",
            id="empty-level",
        ),
        pytest.param(
            file(row(ROOT), row(CHILD, parent=ROOT, validity_from="30-07-2015")),
            "__root__ -> 1 -> gyldig_fra\n  invalid date format",
            id="old-date-format",
        ),
        pytest.param(
            # The reader fills the missing columns of a short row with None
            file(row(ROOT)) + f'"{CHILD}";"{ROOT}"\r\n',
            "__root__ -> 1 -> gyldig_fra\n  none is not an allowed value",
            id="truncated-row",
        ),
        pytest.param(
            file(row(ROOT), row("", parent=ROOT)),
            "__root__ -> 1 -> kode\n  ensure this value has at least 1 characters",
            id="empty-user-key",
        ),
        pytest.param(
            file(row(ROOT), row(CHILD, parent=ROOT, name=" ")),
            "__root__ -> 1 -> navn\n  ensure this value has at least 1 characters",
            id="empty-name",
        ),
        pytest.param(
            file(row(ROOT), row(CHILD, parent=ROOT), row(CHILD, parent=ROOT)),
            f"__root__\n  duplicate kode: {CHILD}",
            id="duplicate-user-key",
        ),
        pytest.param(
            file(row(ROOT), row(CHILD, parent=GRANDCHILD)),
            f"__root__\n  unknown kode_parent: {GRANDCHILD}",
            id="unknown-parent",
        ),
        pytest.param(
            file(row(ROOT, parent=CHILD), row(CHILD, parent=ROOT)),
            "__root__\n  no root, a row without kode_parent",
            id="no-root",
        ),
        pytest.param(
            file(
                row(ROOT), row(CHILD, parent=GRANDCHILD), row(GRANDCHILD, parent=CHILD)
            ),
            f"__root__\n  cycle: {[CHILD, GRANDCHILD, CHILD]}",
            id="cycle",
        ),
    ],
)
def test_invalid_file_is_rejected(text: str, error: str) -> None:
    with pytest.raises(InvalidFile) as exc_info:
        Rows.parse(text)
    assert error in str(exc_info.value)
