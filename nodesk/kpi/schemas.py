from pydantic import BaseModel


class MetricsCardResponse(BaseModel):
    titulo_metrica: str | None = None
    valor_metrica: str | None = None
    top_limit: str | None = None
    bottom_limit: str | None = None
    relation: bool | None = None
