from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..databases import mongo, sqlserver
from ..models import Product, Ticket
from ..settings import Settings

settings = Settings()

OPEN_STATUS_IDS = (1, 2, 3)  # 1=Aberto, 2=Em Atendimento, 3=Aguardando Cliente


def run(limit: int = 10) -> str:
    with Session(sqlserver) as session:
        stmt = (
            select(
                Ticket.product_id,
                Product.name,
                func.count(Ticket.ticket_id).label("open_count"),
            )
            .join(Product, Product.product_id == Ticket.product_id)
            .where(Ticket.current_status_id.in_(OPEN_STATUS_IDS))
            .group_by(Ticket.product_id, Product.name)
            .order_by(func.count(Ticket.ticket_id).desc())
            .limit(limit)
        )
        rows = session.execute(stmt).all()

    doc = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "limit": limit,
        "open_status_ids": list(OPEN_STATUS_IDS),
        "rows": [
            {
                "product_id": pid,
                "product_name": pname,
                "open_tickets": int(count),
            }
            for (pid, pname, count) in rows
        ],
    }
    mongo["critical_projects"].insert_one(doc)
    return f"Inserted snapshot into {settings.MONGO_DB}.critical_projects"
