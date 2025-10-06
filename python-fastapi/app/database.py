from datetime import datetime, timedelta, timezone
from typing import Optional
from secrets import token_urlsafe
from sqlalchemy import Engine, create_engine
from sqlmodel import Field, SQLModel, Session, select

engine: Engine = None


class MagicLink(SQLModel, table=True):
    token: str = Field(primary_key=True)
    email: str
    created: datetime
    expires: datetime

    @classmethod
    def get(cls, token):
        with Session(engine) as session:
            result = session.exec(
                select(MagicLink).where(MagicLink.token == token)
            ).first()
            if result:
                now = datetime.now(timezone.utc)
                if result.created <= now <= result.expires:
                    return result
            return None

    @classmethod
    def delete(cls, magic_link):
        with Session(engine) as session:
            session.delete(magic_link)
            session.commit()

    @classmethod
    def create(cls, email: str, lifetime: timedelta):
        if not email:
            raise ValueError("Magic link must be associated with an email!")
        now = datetime.now(timezone.utc)
        result = MagicLink(
            token=token_urlsafe(36),
            email=email,
            created=now,
            expires=now + lifetime,
        )
        with Session(engine) as session:
            session.add(result)
            session.commit()
        return result


class User(SQLModel, table=True):
    email: str = Field(primary_key=True)
    phone: Optional[str] = None
    name: str = ""

    @classmethod
    def get(cls, email: str):
        with Session(engine) as session:
            return session.exec(select(User).where(User.email == email)).first()

    @classmethod
    def get_or_create(cls, magic_link: MagicLink):
        with Session(engine) as session:
            result = session.exec(
                select(User).where(User.email == magic_link.email)
            ).first()
            if not result:
                result = User(
                    email=magic_link.email,
                )
                session.add(result)
                session.commit()
            return result


def initialize(sqlite_path):
    global engine
    if engine is not None:
        raise ValueError("Database engine has already been initialized!")
    engine = create_engine(
        f"sqlite:///{sqlite_path}", connect_args={"autocommit": False}
    )

    # Note: This will only create tables if they do not exist. It will not change existing tables to match changes in this file.
    # If you want to modify tables while preserving data, consider Alembic: https://alembic.sqlalchemy.org/en/latest/
    SQLModel.metadata.create_all(engine)
