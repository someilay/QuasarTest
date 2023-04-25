from __future__ import annotations

from sqlalchemy import DateTime, String, Engine, exc, ColumnElement, func, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship

from typing import TypeVar
from datetime import datetime, timedelta


class Base(DeclarativeBase):
    """ A base model """
    _T = TypeVar('_T')
    _engine: Engine
    id: Mapped[int] = mapped_column(primary_key=True)

    @classmethod
    def set_engine(cls, engine: Engine):
        """
        Sets a global engine

        :param engine: given engine
        :type engine: Engine
        """
        cls._engine = engine

    def add(self) -> Base | None:
        """
        Add a current object to table

        :return: Object if insertion is successful, otherwise None
        :rtype: T | None
        """
        with Session(self._engine) as session:
            try:
                session.add(self)
                session.commit()
                session.refresh(self)
            except exc.IntegrityError:
                return None
        return self

    @classmethod
    def get(cls: _T, element: ColumnElement) -> _T | None:
        """
        Get an object form a table within a given condition

        :param element: condition, like Base.id == something
        :type element: ColumnElement
        :return: the first row that satisfies condition
        :rtype: T | None
        """
        with Session(cls._engine) as session:
            try:
                stmt = session.query(cls).filter(element)
                return session.scalar(stmt)
            except exc.IntegrityError:
                pass
        return None

    def update(self) -> Base | None:
        """
        Updates a current object in table

        :return: itself or none if case of failure
        :rtype: T | None
        """
        with Session(self._engine) as session:
            try:
                stmt = session.query(type(self)).where(type(self).id == self.id)
                stmt.update(self.__to_raw_dict())
                session.commit()
            except exc.IntegrityError:
                return None
        return self

    @classmethod
    def delete(cls, element: ColumnElement) -> bool:
        """
        Deletes rows that satisfies a given condition

        :param element: condition
        :type element: ColumnElement
        :return: True if at least on element is deleted, in other cases False
        :rtype: bool
        """
        with Session(cls._engine) as session:
            try:
                deleted = session.query(cls).filter(element).delete()
                session.commit()
            except exc.IntegrityError:
                return False
        return deleted > 0

    def __to_raw_dict(self, to_str_int: bool = False) -> dict:
        """
        Converts object to dictionary

        :param to_str_int: indicates that all fields would be converted to int or str
        :type to_str_int: bool
        :return: object as dictionary
        :rtype: dict
        """
        res = dict()
        for column in self.__table__.columns.keys():
            val = getattr(self, column)
            if not isinstance(val, str | int) and to_str_int:
                val = str(val)
            res[column] = val
        return res

    def to_dict(self) -> dict[str, str | int]:
        """
        Converts object to dictionary, all fields are either int or str

        :return: object as dictionary
        :rtype: dict
        """
        return self.__to_raw_dict(True)

    @classmethod
    def pagination(cls: _T, page: int = 0, per_page: int = 10) -> list[_T]:
        """
        Perform pagination, extracting object from table

        :param page: page number
        :type page: int
        :param per_page: object per page
        :type per_page: int
        :return: list of taken objects
        :rtype: list[T]
        """
        with Session(cls._engine) as session:
            return session.query(cls) \
                .order_by(cls.id) \
                .offset(page * per_page) \
                .limit(per_page) \
                .all()

    @classmethod
    def drop_table(cls):
        """Drop table"""
        cls.__table__.drop(cls._engine)

    def __repr__(self) -> str:
        """
        Representation of object

        :return: object as string
        :rtype: str
        """
        return str(self.to_dict())

    def __str__(self) -> str:
        """
        Representation of object

        :return: object as string
        :rtype: str
        """
        return self.__repr__()


class User(Base):
    """User class"""
    _T = TypeVar('_T')
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50))
    registration_date: Mapped[datetime] = mapped_column(DateTime())

    @classmethod
    def registered_last(cls, days: int = 7) -> int:
        """
        Amount of users registered at last n days

        :param days: specifies a search range
        :type days: int
        :return: result
        :rtype: int
        """
        with Session(cls._engine) as session:
            now = datetime.now()
            return session.query(User) \
                .filter(cls.registration_date.between(now - timedelta(days=days), now)) \
                .count()

    @classmethod
    def longest_names(cls: _T, top: int = 5) -> list[_T]:
        """
        List of users with the longest names

        :param top: how many users to return
        :type top: int
        :return: users
        :rtype: list[User]
        """
        with Session(cls._engine) as session:
            return session.query(User) \
                .order_by(func.char_length(User.username).desc()) \
                .limit(top) \
                .all()

    @classmethod
    def percent_emails_endswith(cls, endswith: str) -> float:
        """
        Return a fraction of users that have email ends with a given suffix

        :param endswith: email suffix
        :type endswith: str
        :return: a fraction
        :rtype: float
        """
        with Session(cls._engine) as session:
            c_all = session.query(User).count()
            c_endswith = session.query(User) \
                .filter(cls.email.endswith(endswith)) \
                .count()
            return (c_endswith / c_all) if c_all else 0

    @classmethod
    def delete(cls, element: ColumnElement) -> bool:
        """
        Delete a user, with deletion all activities connected with him

        :param element: condition
        :type element: ColumnElement
        :return: True if at least one object is deleted otherwise False
        :rtype: bool
        """
        with Session(cls._engine) as session:
            try:
                ids = session.query(cls.id).filter(element)
                session.query(Activity).filter(Activity.id.in_(ids)).delete()
                deleted = session.query(cls).filter(element).delete()
                session.commit()
            except exc.IntegrityError:
                return False
        return deleted > 0


class Activity(Base):
    """Activity class"""
    _T = TypeVar('_T')
    __tablename__ = 'activities'

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete='CASCADE'))
    date: Mapped[datetime] = mapped_column(DateTime())

    @classmethod
    def get_activity_by_months(cls, user_id: int, months: int = 12, days_per_m: int = 30) -> list[int]:
        """
        Get list of number of activities within a few last months

        :param user_id: target user id
        :type user_id: int
        :param months: a time range in months
        :type months: int
        :param days_per_m: days per month
        :type days_per_m: int
        :return: number of activities per previous months
        :rtype: list[int]
        """
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

    def add(self) -> Activity | None:
        """
        Add activity to the table, in case if user with connected id exists

        :return: itself in case of success, otherwise None
        :rtype: Activity | None
        """
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
    """
    Setup database

    :param engine: an engine
    :type engine: Engine
    """
    Base.metadata.create_all(engine)
    Base.set_engine(engine)
    User.metadata.create_all(engine)
    Activity.metadata.create_all(engine)
