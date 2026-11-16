# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from itertools import permutations

import pytest

from mo_arbor.code_system_file import HISTORIC_USER_KEY
from mo_arbor.code_system_file import InvalidFile
from mo_arbor.code_system_file import Rows
from mo_arbor.code_system_file import Unit
from mo_arbor.sor import SorRows
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
        validity_to=None,
    )
    child = Unit(
        user_key=CHILD,
        parent=root,
        name="Område",
        org_unit_type="klinisk enhed",
        org_unit_level="N2",
        validity_from=date(2020, 1, 1),
        validity_to=None,
    )
    grandchild = Unit(
        user_key=GRANDCHILD,
        parent=child,
        name="Afdeling",
        org_unit_type="klinisk enhed",
        org_unit_level="N3",
        validity_from=date(2015, 7, 30),
        validity_to=None,
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


def test_start_is_clamped_to_parent_start() -> None:
    """The grandchild is clamped to the child's clamped start."""
    text = file(
        row(ROOT, validity_from="2015-07-30"),
        row(CHILD, parent=ROOT, validity_from="2025-01-09"),
        row(GRANDCHILD, parent=CHILD, validity_from="2015-07-30"),
    )
    units = Rows.parse(text)
    assert units[ROOT].start == date(2015, 7, 30)
    assert units[CHILD].start == date(2025, 1, 9)
    assert units[GRANDCHILD].start == date(2025, 1, 9)
    # Valid under its parent once clamped, so it stays there
    assert HISTORIC_USER_KEY not in units


def test_unit_never_valid_under_parent_goes_under_historic_units() -> None:
    """The grandchild closed before the child started, and keeps its child.

    At the top, even with a single root, so under the code system's root unit.
    """
    text = file(
        row(ROOT, validity_from="2010-01-01"),
        row(CHILD, parent=ROOT, validity_from="2020-01-01"),
        row(
            GRANDCHILD,
            parent=CHILD,
            validity_from="2015-01-01",
            validity_to="2019-12-31",
        ),
        row("GG", parent=GRANDCHILD, validity_from="2016-01-01"),
    )
    units = Rows.parse(text)

    historic = units[HISTORIC_USER_KEY]
    assert historic.parent is None
    assert historic.name == "Historiske enheder"
    assert historic.org_unit_type == "Ukendt"
    assert historic.org_unit_level is None
    assert historic.start == date(1900, 1, 1)
    assert historic.end is None

    assert units[GRANDCHILD].parent is historic
    assert units[GRANDCHILD].start == date(2015, 1, 1)
    assert units[GRANDCHILD].end == date(2019, 12, 31)
    assert units["GG"].parent is units[GRANDCHILD]


def test_start_after_parent_is_kept() -> None:
    text = file(
        row(ROOT, validity_from="2015-07-30"),
        row(CHILD, parent=ROOT, validity_from="2026-05-01"),
    )
    assert Rows.parse(text)[CHILD].start == date(2026, 5, 1)


def test_validity_to() -> None:
    units = Rows.parse(
        file(row(ROOT), row(CHILD, parent=ROOT, validity_to="2030-12-31"))
    )
    assert units[ROOT].end is None
    assert units[CHILD].end == date(2030, 12, 31)


def test_validity_to_on_validity_from() -> None:
    """A unit valid for a single day."""
    units = Rows.parse(
        file(row(ROOT, validity_from="2030-12-31", validity_to="2030-12-31"))
    )
    assert units[ROOT].start == units[ROOT].end == date(2030, 12, 31)


def test_end_is_clamped_to_parent_end() -> None:
    """Open-ended or not, and down the tree."""
    text = file(
        row(ROOT, validity_to="2030-12-31"),
        row(CHILD, parent=ROOT, validity_to="2035-12-31"),
        row(GRANDCHILD, parent=CHILD),
    )
    units = Rows.parse(text)
    assert units[CHILD].end == date(2030, 12, 31)
    assert units[GRANDCHILD].end == date(2030, 12, 31)


def test_end_before_parent_end_is_kept() -> None:
    text = file(
        row(ROOT, validity_to="2030-12-31"),
        row(CHILD, parent=ROOT, validity_to="2029-12-31"),
    )
    assert Rows.parse(text)[CHILD].end == date(2029, 12, 31)


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
            file(row(ROOT, niveau_tekst="Region"), columns=[*COLUMNS, "niveau_tekst"]),
            "__root__ -> 0 -> niveau_tekst\n  extra fields not permitted",
            id="unknown-column",
        ),
        pytest.param(
            file(row(ROOT), columns=[*COLUMNS, "navn"]),
            "duplicate columns: ['navn']",
            id="duplicate-column",
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
            file(row(ROOT), row(CHILD, parent=ROOT, validity_to="31/12/2030")),
            "__root__ -> 1 -> gyldig_til\n  invalid date format",
            id="invalid-validity-to",
        ),
        pytest.param(
            file(row(ROOT), row(CHILD, parent=ROOT, validity_to="2015-07-29")),
            "__root__ -> 1 -> gyldig_til\n  before gyldig_fra",
            id="validity-to-before-validity-from",
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


# Made-up codes in the shape of real ones, with valid check digits
SOR_ROOT = "1001000016005"
SOR_CHILD = "100001000016006"
SOR_SIBLING = "1000001000016004"


def test_sor_codes() -> None:
    text = file(row(SOR_ROOT), row(SOR_CHILD, parent=SOR_ROOT))
    units = SorRows.parse(text)
    assert units[SOR_CHILD].parent_user_key == SOR_ROOT


def test_sor_historic_units_under_root() -> None:
    """Under SOR's single root, so SOR stays one tree, and cut to the root."""
    text = file(
        row(SOR_ROOT, validity_from="2010-01-01"),
        row(SOR_SIBLING, parent=SOR_ROOT, validity_from="2020-01-01"),
        row(
            SOR_CHILD,
            parent=SOR_SIBLING,
            validity_from="2015-01-01",
            validity_to="2019-12-31",
        ),
    )
    units = SorRows.parse(text)

    historic = units[HISTORIC_USER_KEY]
    assert historic.parent is units[SOR_ROOT]
    assert historic.start == date(2010, 1, 1)
    assert units[SOR_CHILD].parent is historic


@pytest.mark.parametrize(
    "text,error",
    [
        pytest.param(
            file(row(SOR_ROOT), row("1,001E+12", parent=SOR_ROOT)),
            "__root__ -> 1 -> kode\n  string does not match regex",
            id="code",
        ),
        pytest.param(
            # SOR_ROOT with its check digit changed from 5 to 6
            file(row(SOR_ROOT), row(SOR_CHILD, parent="1001000016006")),
            "__root__ -> 1 -> kode_parent\n  invalid SOR ID check digit",
            id="parent",
        ),
        pytest.param(
            file(row(SOR_ROOT), row(SOR_SIBLING)),
            f"__root__\n  several roots: {SOR_SIBLING}, {SOR_ROOT}",
            id="several-roots",
        ),
        pytest.param(
            file(
                row(SOR_ROOT, validity_to="2020-12-31"),
                row(SOR_CHILD, parent=SOR_ROOT, validity_from="2021-01-01"),
            ),
            # Under the root itself, so Historiske enheder, which is under the
            # root too, does not help
            f"{SOR_CHILD}: not valid while its parent is",
            id="starts-after-root-ends",
        ),
        pytest.param(
            file(
                row(SOR_ROOT, validity_from="2020-01-01"),
                row(
                    SOR_CHILD,
                    parent=SOR_ROOT,
                    validity_from="2015-01-01",
                    validity_to="2019-12-31",
                ),
            ),
            f"{SOR_CHILD}: not valid while its parent is",
            id="ends-before-root-starts",
        ),
    ],
)
def test_invalid_sor_code_is_rejected(text: str, error: str) -> None:
    with pytest.raises(InvalidFile) as exc_info:
        SorRows.parse(text)
    assert error in str(exc_info.value)
