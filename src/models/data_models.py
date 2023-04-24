from __future__ import annotations

from sqlalchemy import DateTime, String, Engine, exc, ColumnElement, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

from typing import Callable, TypeVar
from datetime import datetime, timedelta


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
        for column in self.__table__.columns.keys():
            val = getattr(self, column)
            if not isinstance(val, str | int) and to_str_int:
                val = str(val)
            res[column] = val
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
    _T = TypeVar('_T')
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50))
    registration_date: Mapped[datetime] = mapped_column(DateTime())

    def __str__(self) -> str:
        return f'{self.id}: {self.username}, {self.email}, {self.registration_date}'

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def registered_last(cls, days: int = 7) -> int:
        with Session(cls._engine) as session:
            return session.query(User)\
                .filter(datetime.now() - cls.registration_date <= timedelta(days=days))\
                .count()

    @classmethod
    def longest_names(cls: _T, top: int = 5) -> list[_T]:
        with Session(cls._engine) as session:
            return session.query(User) \
                .order_by(func.char_length(User.username).desc()) \
                .limit(top)\
                .all()

    @classmethod
    def count_emails_endswith(cls, endswith: str) -> int:
        with Session(cls._engine) as session:
            return session.query(User)\
                .filter(cls.email.endswith(endswith))\
                .count()


def setup(engine: Engine):
    Base.metadata.create_all(engine)
    Base.set_engine(engine)
    User.metadata.create_all(engine)
