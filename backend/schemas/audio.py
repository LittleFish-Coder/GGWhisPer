from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AudioCreate(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    info: str = Field(min_length=1, max_length=1000)


class AudioRead(BaseModel):
    id: int
    title: str = Field(min_length=1, max_length=50)
    info: str = Field(min_length=1, max_length=1000)
    uploaded_date: datetime
    transcript: Dict[str, Any]
    term: Dict[str, Any]


class AudioUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=50)
    info: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    transcript: Optional[Dict[str, Any]] = Field(default=None)
    term: Optional[Dict[str, Any]] = Field(default=None)


class AudioSearch(BaseModel):
    start_date: str
    end_date: str
    title: str
    info: str
    term: str
    transcript: str
