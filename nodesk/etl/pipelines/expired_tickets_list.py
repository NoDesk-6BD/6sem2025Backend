from sqlalchemy import func, literal_column, select, case
from sqlalchemy.orm import Session

from ..databases import mongo, sqlserver
from ..models import SLAPlan, Ticket, Company, User
from ..settings import Settings

settings = Settings()

OPEN_STATUS_IDS = (1, 2, 3)  # 1=Aberto, 2=Em Atendimento, 3=Aguardando Cliente
COLLECTION_NAME = "expired_tickets_list"


def run() -> str:
    with Session(sqlserver) as session:
        # Calcula o deadline: CreatedAt + ResolutionMins
        deadline = func.DATEADD(literal_column("minute"), SLAPlan.resolution_mins, Ticket.created_at)

        # Calcula o tempo vencido em minutos
        tempo_vencido = func.DATEDIFF(literal_column("minute"), deadline, func.GETDATE())

        # Converte IsVIP para texto
        user_vip = case((User.is_vip == True, "Sim"), else_="Não")  # noqa: E712

        stmt = (
            select(
                tempo_vencido.label("tempo_vencido_minutos"),
                Ticket.created_at.label("data_criacao"),
                Ticket.title.label("titulo"),
                Company.name.label("compania_nome"),
                user_vip.label("user_vip"),
            )
            .join(SLAPlan, SLAPlan.sla_plan_id == Ticket.sla_plan_id)
            .join(Company, Company.company_id == Ticket.company_id)
            .join(User, User.user_id == Ticket.created_by_user_id)
            .where(
                Ticket.current_status_id.in_(OPEN_STATUS_IDS),
                Ticket.created_at.isnot(None),
                SLAPlan.resolution_mins.isnot(None),
                deadline < func.GETDATE(),
            )
            .order_by(tempo_vencido.desc())
        )

        results = session.execute(stmt).all()

    # Transforma os resultados em dicionários
    documents = []
    for row in results:
        doc = {
            "tempo_vencido_minutos": int(row.tempo_vencido_minutos) if row.tempo_vencido_minutos else 0,
            "data_criacao": row.data_criacao.isoformat() if row.data_criacao else None,
            "titulo": row.titulo,
            "compania_nome": row.compania_nome,
            "user_vip": row.user_vip,
        }
        documents.append(doc)

    # Limpa a collection e insere os novos dados
    collection = mongo[COLLECTION_NAME]
    collection.delete_many({})

    if documents:
        collection.insert_many(documents)

    return f"Inserted {len(documents)} expired tickets into {settings.MONGO_DB}.{COLLECTION_NAME}"
