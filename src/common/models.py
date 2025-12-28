"""Общие модели для всего приложения"""
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, Mapped, Mapper
from sqlalchemy.engine import Connection

from src.common.database import Base


class SubdomainSettings(Base):
    """Настройки субдомена (timezone и др.)"""

    __tablename__ = "subdomain_settings"

    subdomain: Mapped[str] = mapped_column(sa.String, primary_key=True, index=True)
    timezone: Mapped[str] = mapped_column(sa.String, nullable=False, default="Europe/Moscow")
    created_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime)


@sa.event.listens_for(SubdomainSettings, "before_insert")
def set_created_updated(mapper: Mapper, connection: Connection, target: SubdomainSettings) -> None:
    target.created_at = datetime.now()
    target.updated_at = datetime.now()


@sa.event.listens_for(SubdomainSettings, "before_update")
def set_updated(mapper: Mapper, connection: Connection, target: SubdomainSettings) -> None:
    target.updated_at = datetime.now()
