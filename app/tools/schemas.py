from typing import Literal

from pydantic import BaseModel


class NoteHit(BaseModel):
    path: str
    title: str
    content: str
    hits: int


class EditNoteSuccess(BaseModel):
    ok: Literal[True]
    path: str
    verified: Literal[True]
    bytes: int


class EditNoteFailure(BaseModel):
    ok: Literal[False]
    path: str
    error: list[str]
