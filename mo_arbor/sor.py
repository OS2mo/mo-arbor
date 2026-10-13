# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
"""SOR IDs.

See "Opbygning af SOR-id'er" under "Mere om SOR" on
https://sundhedsdatastyrelsen.dk/data-og-registre/nationale-sundhedsregistre/sundhedsvaesenets-organisationsregister/om-sor
"""

import re

from stdnum import verhoeff

# A running number of any length, the SOR namespace 1000016, the partition ID
# 00 and a Verhoeff check digit
SOR_ID = re.compile(r"[1-9]\d*100001600\d")


def is_sor_id(code: str) -> bool:
    return SOR_ID.fullmatch(code) is not None and verhoeff.is_valid(code)
