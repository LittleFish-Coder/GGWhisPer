from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import DeclarativeBase, mapped_column
from typing import Annotated, Optional
from datetime import datetime


class Base(DeclarativeBase):
    pass


class BaseType:
    uid = Annotated[int, mapped_column(String(10), primary_key=True, unique=True)]
    audio_id = Annotated[
        int, mapped_column(Integer, primary_key=True, unique=True, autoincrement=True)
    ]
    hashed_password = Annotated[str, mapped_column(String(60))]
    str_10 = Annotated[str, mapped_column(String(10))]
    str_50 = Annotated[str, mapped_column(String(50))]
    str_100 = Annotated[str, mapped_column(String(100))]
    str_1000 = Annotated[str, mapped_column(String(1000))]
    datetime = Annotated[datetime, mapped_column(String(60), nullable=True)]
