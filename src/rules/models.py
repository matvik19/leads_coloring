"""Модели базы данных для правил окраски лидов"""
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import JSON
from sqlalchemy.orm import mapped_column, Mapped, Mapper
from sqlalchemy.engine import Connection

from src.common.database import Base


class ColoringRule(Base):
    """Правило окраски лидов"""

    __tablename__ = "coloring_rules"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    subdomain: Mapped[str] = mapped_column(sa.String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    # JSON поле для хранения условий
    # Структура: {"type": "AND"|"OR", "rules": [{"field": "...", "operator": "...", "value": "..."}]}
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False)

    # JSON поле для хранения стилей
    # Структура: {"text_color": "#FFFFFF", "background_color": "#FF0000"}
    style: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime)

    def __repr__(self):
        return f"<ColoringRule(id={self.id}, name={self.name}, subdomain={self.subdomain}, priority={self.priority})>"


@sa.event.listens_for(ColoringRule, "before_insert")
def set_created_updated_rule(mapper: Mapper, connection: Connection, target: ColoringRule) -> None:
    target.created_at = datetime.now()
    target.updated_at = datetime.now()


@sa.event.listens_for(ColoringRule, "before_update")
def set_updated_rule(mapper: Mapper, connection: Connection, target: ColoringRule) -> None:
    target.updated_at = datetime.now()
