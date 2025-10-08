from fastapi import APIRouter, status, Depends, Query, HTTPException
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List, Optional

from ..core.database.session import get_mongo_db
from nodesk.dashboard.schemas import CriticalProjectsSnapshot, TicketsEvolutionResponse
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
    result = []

    for i in range(len(categorias)):
        result.append({"name": categorias[i], "count": counts[i], "abscissa": abscissa})

    obj_result = {"itens": result}

    return obj_result


@dashboard_router.get("/categories", status_code=status.HTTP_200_OK)
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


@dashboard_router.get(
    "/critical_projects",
    response_model=List[CriticalProjectsSnapshot],
    status_code=status.HTTP_200_OK,
)
async def get_critical_projects(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    start: Optional[str] = Query(None, description="ISO 8601 datetime inclusive lower bound"),
    end: Optional[str] = Query(None, description="ISO 8601 datetime inclusive upper bound"),
):
    def parse_iso(value: str) -> datetime:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid datetime format: {value}",
            ) from exc

    filters: dict[str, dict[str, datetime]] = {}

    if start or end:
        parsed_start = parse_iso(start) if start else None
        parsed_end = parse_iso(end) if end else None

        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start must be before or equal to end",
            )

        generated_range: dict[str, datetime] = {}
        if parsed_start:
            generated_range["$gte"] = parsed_start
        if parsed_end:
            generated_range["$lte"] = parsed_end
        filters["generated_at"] = generated_range

    collection = db["critical_projects"]
    documents: List[dict] = []

    if filters:
        cursor = collection.find(filters).sort("generated_at", -1)
        documents = await cursor.to_list(length=None)

        if not documents:
            return []
    else:
        document = await collection.find_one(sort=[("generated_at", -1)])

        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No critical project data found")

        documents = [document]

    for doc in documents:
        doc["id"] = str(doc.pop("_id"))

    return documents
