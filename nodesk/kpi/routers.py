from fastapi import APIRouter, status, HTTPException
import pandas as pd
from prophet.serialize import model_from_json

from nodesk.kpi.schemas import MetricsCardResponse, PredictionRequest


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

    if int(kpi_id) == 3:
        kpi_3 = predict(PredictionRequest(periods=1, freq="W-MON", last_date="2025-01-01"))
        response_kpi_3 = MetricsCardResponse(
            titulo_metrica="Previsão de chamados na próxima semana",
            valor_metrica=str(kpi_3[0]["yhat"]),
            top_limit=str(kpi_3[0]["yhat_upper"]),
            bottom_limit=str(kpi_3[0]["yhat_lower"]),
            relation=False,
        )
        return response_kpi_3

    return kpis[int(kpi_id) - 1]


with open("nodesk/kpi/model/weekly_tickets_model.json", "r") as fin:
    model = model_from_json(fin.read())


def predict(request: PredictionRequest):
    # Lê o CSV
    tickets = pd.read_csv("nodesk/kpi/data/Tickets.csv")

    if tickets.empty:
        raise HTTPException(status_code=404, detail="Nenhum ticket encontrado.")

    # Converte CreatedAt para datetime
    tickets["CreatedAt"] = pd.to_datetime(tickets["CreatedAt"])

    # Agrega por semana (contagem de tickets)
    df = tickets.resample("W-MON", on="CreatedAt").size().reset_index(name="y")
    df.rename(columns={"CreatedAt": "ds"}, inplace=True)

    if df.empty:
        raise HTTPException(status_code=400, detail="Dados insuficientes para previsão.")

    # Gera futuro
    future = model.make_future_dataframe(periods=request.periods, freq=request.freq)

    # Filtra datas maiores que last_date
    last_date = pd.to_datetime(request.last_date)
    future = future[future["ds"] > last_date]

    forecast = model.predict(future)

    # Seleciona as últimas previsões
    result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(request.periods)

    # 🔥 Arredonda todos os valores numéricos para inteiro
    result["yhat"] = result["yhat"].round().astype(int)
    result["yhat_lower"] = result["yhat_lower"].round().astype(int)
    result["yhat_upper"] = result["yhat_upper"].round().astype(int)

    return result.to_dict(orient="records")
