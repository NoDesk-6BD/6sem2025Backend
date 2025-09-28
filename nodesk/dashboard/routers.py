from fastapi import APIRouter, status, Depends
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List, Optional

from ..core.database.session import get_mongo_db
from nodesk.dashboard.schemas import TicketsEvolutionResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

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





# @dashboard_router.get(
#     "/tickets_evolution",
#     response_model=TicketsEvolutionResponse,
#     status_code=status.HTTP_200_OK,
# )
# async def get_tickets_evolution(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
#     return 




    # start_date: Optional[str] = Query(None, description="Data inicial no formato YYYY-MM-DD")
    # end_date: Optional[str] = Query(None, description="Data final no formato YYYY-MM-DD")

    # # Definir intervalo
    # if not start_date or not end_date:
    #     end_date = datetime.today()
    #     start_date = end_date - relativedelta(months=6)
    # else:
    #     start_date = datetime.strptime(start_date, "%Y-%m-%d")
    #     end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # diff_days = (end_date - start_date).days

    # # Determinar granularidade
    # if diff_days >= 120:
    #     group_format = "%Y-%m"  # mês
    #     freq = MONTHLY
    # elif diff_days >= 90:
    #     group_format = "%Y-%U"  # pares de semana (pós-processa)
    #     freq = WEEKLY
    # elif diff_days >= 30:
    #     group_format = "%Y-%U"  # semana
    #     freq = WEEKLY
    # elif diff_days >= 10:
    #     group_format = "%Y-%m-%d"  # pares de dias (pós-processa)
    #     freq = DAILY
    # else:
    #     group_format = "%Y-%m-%d"  # dia
    #     freq = DAILY

    # # Buscar tickets no Mongo
    # pipeline = [
    #     {"$match": {"Data": {"$gte": start_date, "$lte": end_date}}}
    # ]
    # raw_data = list(tickets.aggregate(pipeline))

    # # Criar lista de períodos
    # periodos = list(rrule(freq, dtstart=start_date, until=end_date))
    # periodos_str = [dt.strftime(group_format) for dt in periodos]

    # # Organizar por categoria e período
    # data_dict = defaultdict(lambda: defaultdict(int))
    # for ticket in raw_data:
    #     cat = ticket["Categoria"]
    #     dt = ticket["Data"]

    #     # Determinar o período do ticket
    #     if freq == MONTHLY:
    #         period = dt.strftime("%Y-%m")
    #         days_in_period = (dt.replace(day=28) + relativedelta(days=4)).day  # aproximado 30 dias
    #     elif freq == WEEKLY:
    #         period = dt.strftime("%Y-%U")
    #         days_in_period = 7
    #     else:
    #         period = dt.strftime("%Y-%m-%d")
    #         days_in_period = 1

    #     data_dict[cat][period] += 1

    # # Calcular média somente se dias > 1
    # if freq in [MONTHLY, WEEKLY]:
    #     for cat in data_dict:
    #         for period in data_dict[cat]:
    #             data_dict[cat][period] /= days_in_period

    # # Ordenar categorias
    # categorias = sorted(data_dict.keys())

    # # Construir resultado final
    # result = {
    #     "tickets_by_category": [
    #         {"name": categorias},
    #         {"count": [
    #             [data_dict[cat].get(p, 0) for p in periodos_str] for cat in categorias
    #         ]},
    #         {"abscissa": periodos_str}
    #     ]
    # }

    # return result