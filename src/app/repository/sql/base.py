"""Базовый класс ORM"""

from typing import Dict, Any, Optional, Type, TypeVar, Generic, List, Sequence
from pydantic import BaseModel
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.db.base_class import Base


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый ORM"""

    def __init__(self, model: Type[ModelType], verbose_name: str = "Объект"):
        self.model = model
        self.verbose_name = verbose_name

    async def get(
        self,
        db: AsyncSession,
        obj_id: int,
        *,
        join_relations: Optional[List[str]] = None,
        selectin_relations: Optional[List[str]] = None,
    ) -> Optional[ModelType]:
        """Получение объекта по id"""

        stmt = select(self.model).where(self.model.id == obj_id)
        # JOINs
        if join_relations:
            stmt = stmt.options(
                *(joinedload(getattr(self.model, rel)) for rel in join_relations)
            )
        if selectin_relations:
            stmt = stmt.options(
                *(selectinload(getattr(self.model, rel)) for rel in selectin_relations)
            )

        instance = await db.scalar(stmt)
        if not instance:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"{self.verbose_name} не найден"
            )
        return instance

    async def all(
        self,
        db: AsyncSession,
        *,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        join_relations: Optional[List[str]] = None,
        selectin_relations: Optional[List[str]] = None,
        in_dict: Optional[Dict[str, List]] = None,
        filters_list: Optional[List] = None,
    ) -> Sequence[ModelType]:
        """Получение всех объектов"""

        stmt = select(self.model)

        # Фильтрация
        if in_dict:
            for field, values in in_dict.items():
                if values:
                    stmt = stmt.filter(getattr(self.model, field).in_(values))
        if filters_list:
            stmt = stmt.filter(*filters_list)
        # JOINs
        if join_relations:
            stmt = stmt.options(
                *(joinedload(getattr(self.model, rel)) for rel in join_relations)
            )
        if selectin_relations:
            stmt = stmt.options(
                *(selectinload(getattr(self.model, rel)) for rel in selectin_relations)
            )

        # Пагинация
        if skip:
            stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)

        result = await db.scalars(stmt)
        return result.all()

    async def create(
        self,
        db: AsyncSession,
        data: CreateSchemaType | Dict[str, Any],
        is_return: bool = True,
    ) -> ModelType:
        """
        Создание объекта.
        После создания выполняет refresh всех аттрибутов и связей
        """

        try:
            create_data = data if isinstance(data, dict) else data.model_dump()
            instance = self.model(**create_data)
            db.add(instance)
            await db.commit()

            if is_return:
                await db.refresh(
                    instance,
                    attribute_names=instance.get_attrs_rels_names(),
                )
            return instance
        except IntegrityError as e:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"{self.verbose_name} с такими параметрами уже существует",
            ) from e

    async def bulk_create(
        self,
        db: AsyncSession,
        create_data: List[CreateSchemaType | Dict[str, Any]],
        commit: bool = True,
    ) -> List[ModelType]:
        """Массовое создание объектов"""

        instances = [
            self.model(**(data if isinstance(data, dict) else data.model_dump()))
            for data in create_data
        ]
        db.add_all(instances)
        if commit:
            await db.commit()
        return instances

    async def update(
        self,
        db: AsyncSession,
        instance: ModelType,
        data: UpdateSchemaType | Dict[str, Any],
    ) -> ModelType:
        """
        Обновление объекта.
        После обновления не выполняет refresh
        """
        try:
            update_data = (
                data if isinstance(data, dict) else data.model_dump(exclude_unset=True)
            )

            # Обновляем атрибуты
            for field in instance.get_attributes_names():
                if field in update_data:
                    setattr(instance, field, update_data[field])

            # Обновляем связи
            for relationship in instance.get_relationships_names():
                if relationship in update_data:
                    value = update_data[relationship]
                    if isinstance(value, list):
                        model_relationship = getattr(instance, relationship)
                        model_relationship.clear()
                        model_relationship.extend(value or [])
                    else:
                        setattr(instance, relationship, value)

            db.add(instance)
            await db.commit()
        except IntegrityError as e:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"{self.verbose_name} с такими параметрами уже существует",
            ) from e
        except Exception as e:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Произошла ошибка, обратитесь к администратору",
            ) from e
        return instance

    async def delete(self, db: AsyncSession, instance: ModelType) -> ModelType:
        """Удаление объекта"""

        await db.delete(instance)
        await db.commit()
        return instance
