"""消息按会话与 client_id 联合过滤，禁止跨浏览器 ID 读取。"""

from uuid import uuid4
from database.connection import connect
from database.schema import ensure_schema
from database.conversation_repository import touch_conversation


def list_messages(conversation_id, client_id):
    ensure_schema()
    with connect() as db:
        rows = db.execute("""SELECT m.id, m.role, m.content, m.platform, m.intent, m.execution_mode, m.created_at
            FROM messages m JOIN conversations c ON c.id = m.conversation_id
            WHERE c.id = %s AND c.client_id = %s ORDER BY m.created_at, m.id LIMIT 500""",
            (conversation_id, client_id)).fetchall()
    return [{**row, "id": str(row["id"]), "created_at": row["created_at"].isoformat()} for row in rows]


def save_message(conversation_id, client_id, role, content, platform=None, intent=None, execution_mode=None):
    ensure_schema()
    if role not in ("user", "assistant") or len(content) > 20000:
        raise ValueError("Invalid message")
    with connect() as db:
        row = db.execute("""INSERT INTO messages (id, conversation_id, role, content, platform, intent, execution_mode)
            SELECT %s, c.id, %s, %s, %s, %s, %s FROM conversations c
            WHERE c.id = %s AND c.client_id = %s RETURNING id""",
            (uuid4(), role, content, platform, intent, execution_mode, conversation_id, client_id)).fetchone()
        if row is None:
            raise LookupError("Conversation not found")
        touch_conversation(db, conversation_id, client_id)
