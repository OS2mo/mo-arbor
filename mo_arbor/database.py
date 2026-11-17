# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


class LastIngested(Base):
    """The last dump ingested of each code system.

    A code system has no row until its first ingest.
    """

    __tablename__ = "last_ingested"

    code_system: Mapped[str] = mapped_column(Text, primary_key=True)
    file_name: Mapped[str] = mapped_column(Text)
    # When MO last wrote the dump
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LastReport(Base):
    """The last report uploaded of each code system.

    A code system has no row until its first report.
    """

    __tablename__ = "last_report"

    code_system: Mapped[str] = mapped_column(Text, primary_key=True)
    file_name: Mapped[str] = mapped_column(Text)
    # SHA-256 of the file, to see if a new report differs
    sha256: Mapped[str] = mapped_column(Text)
