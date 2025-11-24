from pydantic import BaseModel


class MetricsCardResponse(BaseModel):
    titulo_metrica: str | None = None
    valor_metrica: str | None = None
    top_limit: str | None = None
    bottom_limit: str | None = None
    relation: bool | None = None


class PredictionRequest(BaseModel):
    periods: int = 12
    freq: str = "W"
    last_date: str
