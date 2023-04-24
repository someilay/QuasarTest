from __future__ import annotations

from sqlalchemy import DateTime, String, Engine, exc, ColumnElement, func, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship

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
                deleted = session.query(cls).filter(element).delete()
                session.commit()
            except exc.IntegrityError:
                return False
        return deleted > 0

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
    def pagination(cls: _T, page: int = 0, per_page: int = 10) -> list[_T]:
        with Session(cls._engine) as session:
            return session.query(cls) \
                .order_by(cls.id) \
                .offset(page * per_page) \
                .limit(per_page) \
                .all()

    @classmethod
    def drop_table(cls):
        cls.__table__.drop(cls._engine)

    def __repr__(self) -> str:
        return str(self.to_dict())

    def __str__(self) -> str:
        return self.__repr__()


class User(Base):
    _T = TypeVar('_T')
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50))
    registration_date: Mapped[datetime] = mapped_column(DateTime())

    @classmethod
    def registered_last(cls, days: int = 7) -> int:
        with Session(cls._engine) as session:
            return session.query(User) \
                .filter(datetime.now() - cls.registration_date <= timedelta(days=days)) \
                .count()

    @classmethod
    def longest_names(cls: _T, top: int = 5) -> list[_T]:
        with Session(cls._engine) as session:
            return session.query(User) \
                .order_by(func.char_length(User.username).desc()) \
                .limit(top) \
                .all()

    @classmethod
    def count_emails_endswith(cls, endswith: str) -> int:
        with Session(cls._engine) as session:
            return session.query(User) \
                .filter(cls.email.endswith(endswith)) \
                .count()


class Activity(Base):
    _T = TypeVar('_T')
    __tablename__ = 'activities'

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete='CASCADE'))
    date: Mapped[datetime] = mapped_column(DateTime())

    @classmethod
    def get_activity_by_months(cls, user_id: int, months: int = 12, days_per_m: int = 30) -> list[int]:
        with Session(cls._engine) as session:
            res = []
            now = datetime.now()
            for i in range(months):
                cur = now - timedelta(days=i * days_per_m)
                prev = now - timedelta(days=(i + 1) * days_per_m)
                res.append(
                    session.query(cls.id)
                    .filter(cls.date.between(prev, cur))
                    .filter(cls.user_id == user_id).count()
                )
            return res

    def add(self) -> Base | None:
        with Session(self._engine) as session:
            if not session.query(User).filter(User.id == self.user_id).scalar():
                return None
            try:
                session.add(self)
                session.commit()
                session.refresh(self)
            except exc.IntegrityError:
                return None
        return self


def setup(engine: Engine):
    engine.echo = False
    Base.metadata.create_all(engine)
    Base.set_engine(engine)
    User.metadata.create_all(engine)
    Activity.metadata.create_all(engine)
