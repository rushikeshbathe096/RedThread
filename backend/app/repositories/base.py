import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic async repository providing reusable CRUD operations (DRY & SOLID).

    Adheres to the Repository Pattern, abstracting data access away from business services.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[List[Any]] = None,
    ) -> List[ModelType]:
        """Fetch multiple records with optional filters and pagination."""
        query = select(self.model)
        if filters:
            for f in filters:
                query = query.where(f)
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        session: AsyncSession,
        *,
        filters: Optional[List[Any]] = None,
    ) -> int:
        """Count total records matching optional filters."""
        query = select(func.count()).select_from(self.model)
        if filters:
            for f in filters:
                query = query.where(f)
        result = await session.execute(query)
        return result.scalar() or 0

    async def create(
        self,
        session: AsyncSession,
        *,
        obj_in: Union[CreateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """Create and persist a new record."""
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump(exclude_unset=True)

        db_obj = self.model(**create_data)
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """Update an existing record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def remove(self, session: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """Delete a record by primary key."""
        obj = await self.get(session, id)
        if obj:
            await session.delete(obj)
            await session.flush()
        return obj
