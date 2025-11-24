from sqlalchemy import select
from sqlalchemy.orm import Session

from ..databases import mongo, sqlserver
from ..models import Company
from ..settings import Settings

settings = Settings()

COLLECTION_NAME = "companies"


def run() -> str:
    """
    ETL pipeline para extrair lista de empresas do SQL Server e carregar no MongoDB.
    """
    print("🚀 Iniciando ETL de Companies...")

    # Extract
    print("📥 Extraindo dados do SQL Server...")
    with Session(sqlserver) as session:
        stmt = select(
            Company.company_id,
            Company.name,
            Company.cnpj,
        )
        results = session.execute(stmt).all()

    # Transform
    print("🔄 Transformando dados...")
    documents = []
    for row in results:
        doc = {
            "company_id": int(row.company_id),
            "name": row.name,
            "cnpj": row.cnpj,
        }
        documents.append(doc)

    # Load
    print("📤 Carregando dados no MongoDB...")
    collection = mongo[COLLECTION_NAME]
    collection.delete_many({})

    if documents:
        collection.insert_many(documents)

    print("✅ Pipeline concluída com sucesso!")
    return f"Inserted {len(documents)} companies into {settings.MONGO_DB}.{COLLECTION_NAME}"
