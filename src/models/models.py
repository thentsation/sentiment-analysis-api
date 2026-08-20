from typing import Annotated

from pydantic import BaseModel, Field

MAX_TEXT_LENGTH = 10_000
MAX_TEXTS = 100


class TextRequest(BaseModel):
    text: Annotated[str, Field(max_length=MAX_TEXT_LENGTH, examples=['I love this!'])]


class MultiTextRequest(BaseModel):
    texts: list[Annotated[str, Field(max_length=MAX_TEXT_LENGTH)]] = Field(
        max_length=MAX_TEXTS, examples=[['I love this!', 'I hate this!']]
    )


class SentimentScores(BaseModel):
    compound: float = Field(description='Normalized aggregate score in [-1, 1]')
    pos: float = Field(description='Positive proportion')
    neu: float = Field(description='Neutral proportion')
    neg: float = Field(description='Negative proportion')


class AnalyzeResponse(BaseModel):
    text: str
    sentiment: SentimentScores


class AnalyzeMultipleResponse(BaseModel):
    results: dict[str, SentimentScores]


class SentimentClassesResponse(BaseModel):
    classes: dict[str, str]


class SentimentStatistics(BaseModel):
    positive: int
    neutral: int
    negative: int


class StatisticsResponse(BaseModel):
    statistics: SentimentStatistics


class HealthResponse(BaseModel):
    status: str


class RootResponse(BaseModel):
    name: str
    version: str
    docs: str
    health: str
    endpoints: list[str]
