from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from prophet.serialize import model_from_json
from nodesk.forecasting.schemas import PredictionRequest
from nodesk.core.database.session import get_db
from nodesk.core.database.models import Ticket

forecasting_router = APIRouter(prefix="/forecasting", tags=["forecasting"])

# Carrega o modelo Prophet salvo
with open("nodesk/forecasting/model/weekly_tickets_model.json", "r") as fin:
    model = model_from_json(fin.read())


@forecasting_router.get("/predict")
def predict(request: PredictionRequest, db: Session = Depends(get_db)):
    # Consulta os tickets do banco
    tickets = db.query(Ticket).filter(Ticket.CreatedAt.isnot(None)).all()

    if not tickets:
        raise HTTPException(status_code=404, detail="Nenhum ticket encontrado no banco.")

    # Converte para DataFrame
    df = pd.DataFrame([{"ds": t.CreatedAt, "y": 1} for t in tickets])
    df = df.resample("W-MON", on="ds").size().reset_index(name="y")

    # Gera previsões
    future = model.make_future_dataframe(periods=request.periods, freq=request.freq)
    future = future[future["ds"] > request.last_date]
    forecast = model.predict(future)

    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(request.periods).to_dict(orient="records")
