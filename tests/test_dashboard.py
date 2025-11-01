from datetime import datetime, timezone
from typing import Any, Optional

import pytest

from nodesk import app
from nodesk.core.database.session import get_mongo_db


class FakeMongoCollection:
    def __init__(self, doc: Optional[dict[str, Any]]):
        self.doc = doc

    async def find_one(self, *args: Any, **kwargs: Any) -> Optional[dict[str, Any]]:
        return self.doc


class FakeMongoDatabase:
    def __init__(self, doc: Optional[dict[str, Any]]):
        self.doc = doc

    def __getitem__(self, name: str) -> FakeMongoCollection:
        return FakeMongoCollection(self.doc)


@pytest.mark.asyncio
async def test_total_expired_tickets_with_snapshot(client):
    snapshot = {
        "_id": "ignored-id",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "total_expired_tickets": 7,
        "open_status_ids": [1, 2, 3],
    }

    async def fake_get_mongo_db():
        yield FakeMongoDatabase(snapshot)

    app.dependency_overrides[get_mongo_db] = fake_get_mongo_db
    try:
        response = await client.get("/dashboard/total_expired_tickets")
    finally:
        app.dependency_overrides.pop(get_mongo_db, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_expired_tickets"] == 7
    assert payload["open_status_ids"] == [1, 2, 3]
    assert "generated_at" in payload and payload["generated_at"]


@pytest.mark.asyncio
async def test_total_expired_tickets_without_snapshot(client):
    async def fake_get_mongo_db():
        yield FakeMongoDatabase(None)

    app.dependency_overrides[get_mongo_db] = fake_get_mongo_db
    try:
        response = await client.get("/dashboard/total_expired_tickets")
    finally:
        app.dependency_overrides.pop(get_mongo_db, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_expired_tickets"] == 0
    assert payload["open_status_ids"] == [1, 2, 3]
    assert payload["generated_at"] is None
