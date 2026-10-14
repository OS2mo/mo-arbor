# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import date

import pytest

from mo_arbor.code_system_file import InvalidFile
from mo_arbor.code_system_file import Unit
from mo_arbor.code_system_file import parse
from mo_arbor.sor import is_sor_id
from tests.helpers import COLUMNS
from tests.helpers import file
from tests.helpers import row

ROOT = "R"
CHILD = "C"
GRANDCHILD = "G"


def tree(
    root_from: str = "2015-07-30",
    child_from: str = "2015-07-30",
    grandchild_from: str = "2015-07-30",
) -> str:
    return file(
        row(ROOT, name="Root", org_unit_type="region", validity_from=root_from),
        row(
            CHILD,
            parent=ROOT,
            name="Område",
            org_unit_level="N2",
            validity_from=child_from,
        ),
        row(
            GRANDCHILD,
            parent=CHILD,
            name="Afdeling",
            org_unit_level="N3",
            validity_from=grandchild_from,
        ),
    )


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
    units = parse(text)

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
    assert units[GRANDCHILD].parent is units[CHILD]
    assert units[GRANDCHILD].parent_user_key == CHILD
    assert [units[k].depth for k in (ROOT, CHILD, GRANDCHILD)] == [1, 2, 3]


def test_other_columns_are_ignored() -> None:
    """Such as aktiv and dw_is_deleted."""
    text = file(
        row(ROOT, aktiv="false", dw_is_deleted="true"),
        row(CHILD, parent=ROOT),
    )
    assert parse(text).keys() == {ROOT, CHILD}


def test_parse_without_quotes_and_crlf() -> None:
    text = file(row(ROOT), row(CHILD, parent=ROOT))
    text = text.replace('"', "").replace("\r\n", "\n")
    assert parse(text).keys() == {ROOT, CHILD}


def test_start_is_clamped_to_parent_start() -> None:
    """The grandchild is clamped to the child's clamped start."""
    units = parse(tree(child_from="2025-01-09", grandchild_from="2015-07-30"))
    assert units[ROOT].start == date(2015, 7, 30)
    assert units[CHILD].start == date(2025, 1, 9)
    assert units[GRANDCHILD].start == date(2025, 1, 9)


def test_start_after_parent_is_kept() -> None:
    units = parse(tree(grandchild_from="2026-05-01"))
    assert units[GRANDCHILD].start == date(2026, 5, 1)


def test_validity_to() -> None:
    units = parse(file(row(ROOT), row(CHILD, parent=ROOT, validity_to="2030-12-31")))
    assert units[ROOT].end is None
    assert units[CHILD].end == date(2030, 12, 31)


def test_validity_to_on_validity_from() -> None:
    """A unit valid for a single day."""
    units = parse(file(row(ROOT, validity_from="2030-12-31", validity_to="2030-12-31")))
    assert units[ROOT].start == units[ROOT].end == date(2030, 12, 31)


def test_end_is_clamped_to_parent_end() -> None:
    """Open-ended or not, and down the tree."""
    text = file(
        row(ROOT, validity_to="2030-12-31"),
        row(CHILD, parent=ROOT, validity_to="2035-12-31"),
        row(GRANDCHILD, parent=CHILD),
    )
    units = parse(text)
    assert units[CHILD].end == date(2030, 12, 31)
    assert units[GRANDCHILD].end == date(2030, 12, 31)


def test_end_before_parent_end_is_kept() -> None:
    text = file(
        row(ROOT, validity_to="2030-12-31"),
        row(CHILD, parent=ROOT, validity_to="2029-12-31"),
    )
    assert parse(text)[CHILD].end == date(2029, 12, 31)


def test_several_roots() -> None:
    units = parse(file(row(ROOT), row(CHILD), row(GRANDCHILD, parent=CHILD)))
    assert {k: u.depth for k, u in units.items()} == {ROOT: 1, CHILD: 1, GRANDCHILD: 2}


def test_rows_in_any_order() -> None:
    text = file(row(GRANDCHILD, parent=CHILD), row(CHILD, parent=ROOT), row(ROOT))
    units = parse(text)
    assert {k: u.depth for k, u in units.items()} == {ROOT: 1, CHILD: 2, GRANDCHILD: 3}


def test_values_are_stripped() -> None:
    text = file(row(ROOT), row(f" {CHILD} ", parent=f"{ROOT} ", name=" Afdeling "))
    assert parse(text)[CHILD].name == "Afdeling"
    assert parse(text)[CHILD].parent_user_key == ROOT


@pytest.mark.parametrize(
    "text,error",
    [
        pytest.param(
            "", "__root__\n  no root, a row without kode_parent", id="empty-file"
        ),
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
            file(
                row(ROOT, validity_to="2020-12-31"),
                row(CHILD, parent=ROOT, validity_from="2021-01-01"),
            ),
            f"{CHILD}: not valid while its parent is",
            id="starts-after-parent-ends",
        ),
        pytest.param(
            file(
                row(ROOT, validity_from="2020-01-01"),
                row(
                    CHILD,
                    parent=ROOT,
                    validity_from="2015-01-01",
                    validity_to="2019-12-31",
                ),
            ),
            f"{CHILD}: not valid while its parent is",
            id="ends-before-parent-starts",
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
            f"__root__\n  unknown kode_parent in: {CHILD}",
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
            f"__root__\n  not under a root: {CHILD}, {GRANDCHILD}",
            id="cycle",
        ),
    ],
)
def test_invalid_file_is_rejected(text: str, error: str) -> None:
    with pytest.raises(InvalidFile) as exc_info:
        parse(text)
    assert error in str(exc_info.value)


# Made-up codes in the shape of real ones, with valid check digits
SOR_ROOT = "1001000016005"
SOR_CHILD = "100001000016006"


def test_sor_codes() -> None:
    text = file(row(SOR_ROOT), row(SOR_CHILD, parent=SOR_ROOT))
    units = parse(text, is_sor_id)
    assert units[SOR_CHILD].parent_user_key == SOR_ROOT


def test_invalid_sor_code_is_rejected() -> None:
    text = file(row(SOR_ROOT), row("1,001E+12", parent=SOR_ROOT))
    with pytest.raises(InvalidFile) as exc_info:
        parse(text, is_sor_id)
    assert str(exc_info.value) == "invalid codes: ['1,001E+12']"
