from datetime import datetime, timezone

from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Session

from ..databases import mongo, sqlserver
from ..models import SLAPlan, Ticket
from ..settings import Settings

settings = Settings()

OPEN_STATUS_IDS = (1, 2, 3)  # 1=Aberto, 2=Em Atendimento, 3=Aguardando Cliente
COLLECTION_NAME = "expired_tickets_totals"


def run() -> str:
    with Session(sqlserver) as session:
        deadline = func.DATEADD(literal_column("minute"), SLAPlan.resolution_mins, Ticket.created_at)

        stmt = (
            select(func.count(Ticket.ticket_id))
            .join(SLAPlan, SLAPlan.sla_plan_id == Ticket.sla_plan_id)
            .where(
                Ticket.current_status_id.in_(OPEN_STATUS_IDS),
                Ticket.created_at.isnot(None),
                SLAPlan.resolution_mins.isnot(None),
                deadline < func.GETDATE(),
            )
        )

        total_expired = session.execute(stmt).scalar_one()

    doc = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "open_status_ids": list(OPEN_STATUS_IDS),
        "total_expired_tickets": int(total_expired),
    }
    mongo[COLLECTION_NAME].insert_one(doc)

    return f"Inserted snapshot into {settings.MONGO_DB}.{COLLECTION_NAME}"
