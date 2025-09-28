from pydantic import BaseModel
from typing import List

class TicketsEvolutionItem(BaseModel):
    name: List[str] | None = None
    count: List[List[int]] | None = None
    abscissa: List[str] | None = None

class TicketsEvolutionResponse(BaseModel):
    tickets_evolution: List[TicketsEvolutionItem]
