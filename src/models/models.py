from pydantic import BaseModel


class TextRequest(BaseModel):
    text: str

class MultiTextRequest(BaseModel):
    texts: list[str]