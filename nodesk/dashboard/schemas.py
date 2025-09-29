from pydantic import BaseModel
from typing import List

class TicketsEvolutionItem(BaseModel):
    name: str | None = None
    count: List[int]| None = None
    abscissa: List[str] | None = None

class TicketsEvolutionResponse(BaseModel):
    itens: List[TicketsEvolutionItem]
