from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TicketsEvolutionItem(BaseModel):
    name: str | None = None
    count: List[int] | None = None
    abscissa: List[str] | None = None


class TicketsEvolutionResponse(BaseModel):
    itens: List[TicketsEvolutionItem]


class CriticalProjectRow(BaseModel):
    product_id: int
    product_name: str
    open_tickets: int


class CriticalProjectsSnapshot(BaseModel):
    id: str
    generated_at: datetime
    limit: int
    open_status_ids: List[int]
    rows: List[CriticalProjectRow]


class TotalExpiredTicketsResponse(BaseModel):
    generated_at: Optional[datetime] = None
    total_expired_tickets: int
    open_status_ids: List[int]
