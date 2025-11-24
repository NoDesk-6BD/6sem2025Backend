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


class ExpiredTicketItem(BaseModel):
    tempo_vencido_minutos: int
    data_criacao: Optional[datetime] = None
    titulo: str
    compania_id: int
    compania_nome: str
    user_vip: str


class ExpiredTicketsListResponse(BaseModel):
    items: List[ExpiredTicketItem]
    total: int
    limit: int
    offset: int


class CompanyItem(BaseModel):
    company_id: int
    name: str
    cnpj: Optional[str] = None


class CompaniesListResponse(BaseModel):
    companies: List[CompanyItem]
