from fastapi import APIRouter, HTTPException
import pandas as pd
from prophet.serialize import model_from_json
from nodesk.forecasting.schemas import PredictionRequest

forecasting_router = APIRouter(prefix="/forecasting", tags=["forecasting"])

# Carrega o modelo Prophet salvo
with open("nodesk/forecasting/model/weekly_tickets_model.json", "r") as fin:
    model = model_from_json(fin.read())


@forecasting_router.post("/predict")
def predict(request: PredictionRequest):
    # Lê o CSV
    tickets = pd.read_csv("nodesk/forecasting/data/Tickets.csv")

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

    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(request.periods).to_dict(orient="records")
