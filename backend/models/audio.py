from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from sqlalchemy.types import JSON

from models.base import Base, BaseType


class Audio(Base):
    __tablename__ = "Audio"
    id: Mapped[BaseType.audio_id]
    title: Mapped[BaseType.str_50]
    info: Mapped[BaseType.str_1000]
    uploaded_date: Mapped[BaseType.datetime]
    transcript: Mapped[JSON] = mapped_column(JSON, nullable=True)
    term: Mapped[JSON] = mapped_column(JSON, nullable=True)
