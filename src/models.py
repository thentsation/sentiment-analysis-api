from pydantic import BaseModel
from typing import List

class TextRequest(BaseModel):
    text: str

class MultiTextRequest(BaseModel):
    texts: List[str]
