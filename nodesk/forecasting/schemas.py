from pydantic import BaseModel


class PredictionRequest(BaseModel):
    periods: int = 12
    freq: str = "W"
    last_date: str
