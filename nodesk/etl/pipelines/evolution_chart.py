import datetime
import pandas as pd
from datetime import timedelta
from collections import Counter

from ..databases import mongo, sqlserver


def extract_sqlserver_for_evolution_chart():
    """
    Extrai dados do SQL Server usando SQLAlchemy para evitar warnings do pandas.
    Retorna o df da primeira data e df dos tickets (histórico completo).
    """

    # Query para pegar a primeira data
    query_first_date = """
    SELECT TOP 1 Tickets.CreatedAt AS FirstCreatedAt
    FROM Tickets
    ORDER BY Tickets.CreatedAt ASC;
    """
    df_first_date = pd.read_sql(query_first_date, sqlserver)

    # Query para pegar histórico completo de tickets
    query_tickets = """
    SELECT Tickets.TicketId, FromStatusId, ToStatusId, ChangedAt,
           Categories.Name AS Category, Subcategories.Name AS Subcategories, CreatedAt
    FROM Tickets
    LEFT JOIN TicketStatusHistory ON TicketStatusHistory.TicketId = Tickets.TicketId
    JOIN Categories ON Tickets.CategoryId = Categories.CategoryId
    JOIN Subcategories ON Tickets.SubcategoryId = Subcategories.SubcategoryId
    """
    df_tickets = pd.read_sql(query_tickets, sqlserver)

    # Debug rápido
    print("df_tickets (preview):")
    print(df_tickets.head(3))

    return df_first_date, df_tickets


def normalize_date(doc):
    if isinstance(doc, datetime.date) and not isinstance(doc, datetime.datetime):
        doc = datetime.datetime.combine(doc, datetime.time.min)
    return doc


def transform_tickets(df_first_date, df_tickets):
    start_date = pd.to_datetime(df_first_date.iloc[0, 0]).date()
    end_date = pd.Timestamp.today().date()

    # PARA TESTES
    # start_date = pd.Timestamp("2025-09-04").date()
    # end_date = start_date + timedelta(days=2)

    open_tickets = {}  # dict: {TicketId: {"TicketId": ..., "Categoria": ..., "Subcategoria": ...}}
    evolution = []

    current_date = start_date

    while current_date <= end_date:
        print("current_date", current_date, "\n")
        current_date_ts = pd.Timestamp(current_date)

        # Tickets criados hoje
        created_today = df_tickets[pd.to_datetime(df_tickets["CreatedAt"]).dt.normalize() == current_date_ts]

        # Tickets que mudaram para status aberto, em atendimento, aguardando cliente hoje
        changed_today = df_tickets[
            (pd.to_datetime(df_tickets["ChangedAt"]).dt.normalize() == current_date_ts)
            & (df_tickets["ToStatusId"].isin([1, 2, 3]))
        ]

        # Todos os tickets que devem ser adicionados
        to_add = pd.concat([created_today, changed_today])

        for _, row in to_add.iterrows():
            open_tickets[row["TicketId"]] = {
                "TicketId": row["TicketId"],
                "Categoria": row["Category"],
                "Subcategoria": row["Subcategories"],
            }

        # Tickets fechados hoje
        closed_today = df_tickets[
            (pd.to_datetime(df_tickets["ChangedAt"]).dt.normalize() == current_date_ts)
            & (df_tickets["ToStatusId"].isin([4, 5]))
        ]

        for _, row in closed_today.iterrows():
            open_tickets.pop(row["TicketId"], None)  # remove se existir

        # Contagem de categorias e subcategorias
        categories_count = Counter([t["Categoria"] for t in open_tickets.values()])
        subcategories_count = Counter([t["Subcategoria"] for t in open_tickets.values()])

        # Salvar a evolução do dia
        date_to_bson = normalize_date(current_date)
        evolution.append(
            {
                "date": date_to_bson,
                "categories_count": dict(categories_count),
                "subcategories_count": dict(subcategories_count),
                # "tickets": list(open_tickets.values())
            }
        )

        # Próximo dia
        current_date += timedelta(days=1)

    return evolution


def load_evolution_to_mongo(evolution, collection_name):
    collection = mongo[collection_name]
    collection.delete_many({})
    collection.insert_many(evolution)


def evolution_chart_pipeline():
    print("🚀 Iniciando ETL do Evolution Chart...")

    # Extract
    print("📥 Extraindo dados do SQL Server...")
    df_first_date, df_tickets = extract_sqlserver_for_evolution_chart()

    # Transform
    print("🔄 Transformando dados...")
    evolution = transform_tickets(df_first_date, df_tickets)

    # Load
    print("📤 Carregando dados no MongoDB...")
    load_evolution_to_mongo(evolution, collection_name="tickets_evolution")

    print("✅ Pipeline concluída com sucesso!")
