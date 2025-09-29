from fastapi import APIRouter, status, Depends, Query
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List, Optional

from ..core.database.session import get_mongo_db
from nodesk.dashboard.schemas import TicketsEvolutionResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
import pandas as pd

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@dashboard_router.get("/exemplo", response_model=List[dict])
async def exemplo(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """
    Retorna os 3 primeiros documentos da collection tickets_evolution
    """
    collection = db["tickets_evolution"]

    # Pega os 3 primeiros documentos
    dados = await collection.find().to_list(length=3)

    # Converte os ObjectId para string
    for doc in dados:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])

    return dados


@dashboard_router.get(
    "/tickets_evolution",
    response_model=TicketsEvolutionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_tickets_evolution(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    if not start_date or not end_date:
        end = datetime.today().date()
        start = end - relativedelta(months=6)
    else:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

    diff_days = (end - start).days

    # Define granularidade
    if diff_days >= 120:
        granularity = "M"  # mês
    elif diff_days >= 90:
        granularity = "2W"  # pares de semanas
    elif diff_days >= 30:
        granularity = "W"  # semana
    elif diff_days >= 10:
        granularity = "2D"  # pares de dias
    else:
        granularity = "D"  # dia

    # Busca os dados no Mongo
    collection = db["tickets_evolution"]
    cursor = collection.find(
        {
            "date": {
                "$gte": datetime.combine(start, datetime.min.time()),
                "$lte": datetime.combine(end, datetime.max.time()),
            }
        }
    )
    docs = await cursor.to_list(length=None)

    # se não houver documentos, retorne no formato esperado pelo pydantic
    if not docs:
        return {"tickets_evolution": []}

    # Normaliza em DataFrame (cada coluna = uma categoria)
    df = pd.DataFrame([{"date": pd.to_datetime(doc["date"]), **doc["categories_count"]} for doc in docs]).set_index(
        "date"
    )

    # Resample de acordo com granularidade (média para agregações maiores, diário mantém)
    if granularity in ["M", "W", "2W", "2D"]:
        df_grouped = df.resample(granularity).mean().fillna(0)
    elif granularity == "D":
        # já está diário no índice; garantir ordenação por data
        df_grouped = df.sort_index()
    else:
        df_grouped = df.sort_index()

    # Converter para inteiros (arredonda médias)
    df_int = df_grouped.round().astype(int)

    # Preparar saída
    categorias = list(df_int.columns)
    counts = [df_int[cat].tolist() for cat in categorias]

    # Abscissa (labels do eixo x)
    if granularity == "M":
        abscissa = [d.strftime("%b/%Y") for d in df_int.index]
    elif granularity in ["W", "2W"]:
        abscissa = [f"Sem {d.strftime('%U')}/{d.year}" for d in df_int.index]
    elif granularity in ["2D", "D"]:
        abscissa = [d.strftime("%d/%m") for d in df_int.index]
    else:
        abscissa = [str(d.date()) for d in df_int.index]

    # Montar resposta no formato esperado por TicketsEvolutionResponse
    result = {"tickets_evolution": [{"name": categorias, "count": counts, "abscissa": abscissa}]}

    return result


@dashboard_router.get("/top_subcategories", status_code=status.HTTP_200_OK)
async def top_subcategories(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    end = datetime.today().date() if not end_date else datetime.strptime(end_date, "%Y-%m-%d").date()
    start = end - relativedelta(days=60) if not start_date else datetime.strptime(start_date, "%Y-%m-%d").date()

    collection = db["tickets_evolution"]
    cursor = collection.find(
        {
            "date": {
                "$gte": datetime.combine(start, datetime.min.time()),
                "$lte": datetime.combine(end, datetime.max.time()),
            }
        }
    )
    docs = await cursor.to_list(length=None)

    if not docs:
        return []

    subcategories_sum = {}
    for doc in docs:
        for subcat, count in doc.get("subcategories_count", {}).items():
            subcategories_sum[subcat] = subcategories_sum.get(subcat, 0) + count

    num_days = (end - start).days + 1

    subcategories_avg = {name: total / num_days for name, total in subcategories_sum.items()}

    top5 = sorted(subcategories_avg.items(), key=lambda x: x[1], reverse=True)[:5]

    result = [{"name": name, "count": int(round(count))} for name, count in top5]

    return result
