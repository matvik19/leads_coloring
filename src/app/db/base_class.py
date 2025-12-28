from typing import Any
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr


class Base(AsyncAttrs, DeclarativeBase):
    metadata = MetaData()

    id: Any

    __name__: str

    @declared_attr
    @classmethod
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    @classmethod
    def get_attributes_names(cls):
        return cls.__mapper__.column_attrs.keys()

    @classmethod
    def get_relationships_names(cls):
        return cls.__mapper__.relationships.keys()

    @classmethod
    def get_attrs_rels_names(cls):
        return [*cls.get_attributes_names(), *cls.get_relationships_names()]
