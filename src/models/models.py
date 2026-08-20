from typing import Annotated

from pydantic import BaseModel, Field

MAX_TEXT_LENGTH = 10_000
MAX_TEXTS = 100


class TextRequest(BaseModel):
    text: str = Field(max_length=MAX_TEXT_LENGTH)


class MultiTextRequest(BaseModel):
    texts: list[Annotated[str, Field(max_length=MAX_TEXT_LENGTH)]] = Field(
        max_length=MAX_TEXTS
    )
