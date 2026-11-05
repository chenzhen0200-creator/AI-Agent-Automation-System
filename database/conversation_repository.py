"""所有会话读写都绑定匿名 client_id。"""

from uuid import uuid4
from database.connection import connect
from database.schema import ensure_schema


def _public(row):
    return {**row, "id": str(row["id"]), "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat()}


def list_conversations(client_id):
    ensure_schema()
    with connect() as db:
        rows = db.execute("SELECT id, title, created_at, updated_at FROM conversations WHERE client_id = %s ORDER BY updated_at DESC LIMIT 100", (client_id,)).fetchall()
    return [_public(row) for row in rows]


def get_conversation(conversation_id, client_id):
    ensure_schema()
    with connect() as db:
        row = db.execute("SELECT id, title, created_at, updated_at FROM conversations WHERE id = %s AND client_id = %s", (conversation_id, client_id)).fetchone()
    return _public(row) if row else None


def create_conversation(client_id, title):
    ensure_schema()
    conversation_id = uuid4()
    with connect() as db:
        row = db.execute("INSERT INTO conversations (id, client_id, title) VALUES (%s, %s, %s) RETURNING id, title, created_at, updated_at", (conversation_id, client_id, title[:100])).fetchone()
    return _public(row)


def delete_conversation(conversation_id, client_id):
    ensure_schema()
    with connect() as db:
        row = db.execute("DELETE FROM conversations WHERE id = %s AND client_id = %s RETURNING id", (conversation_id, client_id)).fetchone()
    return row is not None


def touch_conversation(db, conversation_id, client_id):
    db.execute("UPDATE conversations SET updated_at = NOW() WHERE id = %s AND client_id = %s", (conversation_id, client_id))
