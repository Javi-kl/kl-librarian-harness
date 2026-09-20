from pydantic import BaseModel


class NoteHit(BaseModel):
    path: str
    title: str
    content: str
    hits: int
