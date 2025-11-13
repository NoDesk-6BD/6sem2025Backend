from fastapi import APIRouter, status, HTTPException

from nodesk.kpi.schemas import (
    MetricsCardResponse,
)


kpi_router = APIRouter(prefix="/kpi", tags=["kpi"])


@kpi_router.get("/{kpi_id}", response_model=MetricsCardResponse, status_code=status.HTTP_200_OK)
async def kpi(kpi_id: str):
    """
    Retorna o KPI mockado
    """

    if not kpi_id.isdigit():
        raise HTTPException(status_code=400, detail="ID inválido")

    if kpi_id not in ["1", "2", "3", "4"]:
        raise HTTPException(status_code=404, detail="KPI não encontrado")

    kpis = [
        {
            "titulo_metrica": "Tickets Resolvidos",
            "valor_metrica": "15",
            "top_limit": "20",
            "bottom_limit": "10",
            "relation": False,
        },
        {
            "titulo_metrica": "Tempo médio de atendimento",
            "valor_metrica": "18:53",
            "top_limit": "72:00",
            "bottom_limit": "8:00",
            "relation": False,
        },
        {
            "titulo_metrica": "Tickets Resolvidos",
            "valor_metrica": "15",
            "top_limit": "20",
            "bottom_limit": "10",
            "relation": False,
        },
        {
            "titulo_metrica": "Tickets Abertos",
            "valor_metrica": "5",
            "top_limit": "10",
            "bottom_limit": "2",
            "relation": False,
        },
    ]

    return kpis[int(kpi_id) - 1]
