from __future__ import annotations

from sqlalchemy import DateTime, String, Engine, exc, ColumnElement
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Session

from typing import Callable, TypeVar
from datetime import datetime


class Base(DeclarativeBase):
    _T = TypeVar('_T')
    _engine: Engine
    id: Mapped[int] = mapped_column(primary_key=True)

    @classmethod
    def set_engine(cls, engine: Engine):
        cls._engine = engine

    def add(self) -> Base | None:
        with Session(self._engine) as session:
            try:
                session.add(self)
                session.commit()
                session.refresh(self)
            except exc.IntegrityError:
                return None
        return self

    @classmethod
    def get(cls: _T, element: ColumnElement | None) -> _T | None:
        with Session(cls._engine) as session:
            try:
                stmt = session.query(cls).filter(element)
                return session.scalar(stmt)
            except exc.IntegrityError:
                pass
        return None

    def update(self) -> Base | None:
        with Session(self._engine) as session:
            try:
                stmt = session.query(type(self)).where(type(self).id == self.id)
                stmt.update(self.__to_raw_dict())
                session.commit()
            except exc.IntegrityError:
                return None
        return self

    @classmethod
    def delete(cls, element: ColumnElement | None) -> bool:
        with Session(cls._engine) as session:
            try:
                session.query(cls).filter(element).delete()
                session.commit()
            except exc.IntegrityError:
                return False
        return True

    def __to_raw_dict(self, to_str_int: bool = False):
        res = dict()
        for key, val in vars(self).items():
            if isinstance(val, Callable) or key.startswith('_'):
                continue
            if not isinstance(val, str | int) and to_str_int:
                val = str(val)
            res[key] = val
        return res

    def to_dict(self) -> dict[str, str | int]:
        return self.__to_raw_dict(True)

    @classmethod
    def pagination(cls: _T, page: int, per_page: int) -> list[_T]:
        with Session(cls._engine) as session:
            return session.query(cls)\
                .order_by(cls.id) \
                .offset(page * per_page) \
                .limit(per_page) \
                .all()


class User(Base):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50))
    registration_date: Mapped[datetime] = mapped_column(DateTime())

    def __str__(self) -> str:
        return f'{self.id}: {self.username}, {self.email}, {self.registration_date}'


def setup(engine: Engine):
    Base.metadata.create_all(engine)
    Base.set_engine(engine)
    User.metadata.create_all(engine)
