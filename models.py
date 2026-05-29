from enum import StrEnum
from pydantic import BaseModel, Field


class Action(StrEnum):
    create = "create"
    delete = "delete"
    update = "update"


class Time(BaseModel):
    year: int
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    second: int = Field(default=0, ge=0, le=59)


class Event(BaseModel):
    action: Action = Field(description="用户想执行的日程操作")
    title: str = Field(description="The title of the event.")
    start: Time = Field(description="The start time of the event.")
    end: Time = Field(description="The end time of the event.")
    location: str | None = Field(description="The location of the event.")
    description: str | None = Field(description="A description of the event.")
