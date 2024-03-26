from __future__ import annotations
import uuid
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, String, UUID, DateTime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from typing import List


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(Base):
    __tablename__ = "user_table"

    email: Mapped[str] = mapped_column(String(40), primary_key=True)
    password: Mapped[str]
    connections: Mapped[List["Connection"]] = relationship(back_populates="user")
    logevent: Mapped[List["LogEvent"]] = relationship(back_populates="user")

class Connection(Base):
    __tablename__ = "connection_table"

    cid: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_email: Mapped[str] = mapped_column(ForeignKey("user_table.email"))
    user: Mapped["User"] = relationship(back_populates="connections")
    device: Mapped[str]


class LogEvent(Base):
    __tablename__ = "logevent_table"

    eid: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_email: Mapped[str] = mapped_column(ForeignKey("user_table.email"))
    user: Mapped["User"] = relationship(back_populates="logevent")
    time: Mapped[datetime.datetime]
    event_desc: Mapped[str]
    ip: Mapped[str]
    location: Mapped[str]
    device: Mapped[str]
