"""消息按会话与 client_id 联合过滤，禁止跨浏览器 ID 读取。"""

from uuid import uuid4
from psycopg.types.json import Jsonb
from database.connection import connect
from database.schema import ensure_schema
from database.conversation_repository import touch_conversation
from tools.visual_steps import attach_images


def list_messages(conversation_id, client_id):
    ensure_schema()
    with connect() as db:
        rows = db.execute("""SELECT m.id, m.role, m.content, m.platform, m.intent, m.execution_mode, m.metadata, m.created_at
            FROM messages m JOIN conversations c ON c.id = m.conversation_id
            WHERE c.id = %s AND c.client_id = %s ORDER BY m.created_at, m.id LIMIT 500""",
            (conversation_id, client_id)).fetchall()
    messages = []
    for row in rows:
        message = {**row, "id": str(row["id"]), "created_at": row["created_at"].isoformat()}
        metadata = message.get("metadata")
        if isinstance(metadata, dict) and metadata.get("intent") == "steps" and isinstance(metadata.get("steps"), list):
            metadata = dict(metadata)
            steps = [dict(step) for step in metadata["steps"] if isinstance(step, dict)]
            variant = metadata.get("image_variant")
            # 旧历史只有模拟图 URL；根据原路径恢复“复制广告组”主题后清除 URL。
            if variant is None and any("/ad-set-duplicate/" in str(step.get("image_url")) for step in steps):
                variant = "Ad Set Duplicate"
            metadata["image_variant"] = variant
            metadata["steps"] = attach_images(steps, metadata.get("platform"), metadata.get("topic"), variant)
            message["metadata"] = metadata
        messages.append(message)
    return messages


def save_message(conversation_id, client_id, role, content, platform=None, intent=None, execution_mode=None, metadata=None):
    ensure_schema()
    if role not in ("user", "assistant") or len(content) > 20000:
        raise ValueError("Invalid message")
    with connect() as db:
        row = db.execute("""INSERT INTO messages (id, conversation_id, role, content, platform, intent, execution_mode, metadata)
            SELECT %s, c.id, %s, %s, %s, %s, %s, %s FROM conversations c
            WHERE c.id = %s AND c.client_id = %s RETURNING id""",
            (uuid4(), role, content, platform, intent, execution_mode, Jsonb(metadata) if metadata else None,
             conversation_id, client_id)).fetchone()
        if row is None:
            raise LookupError("Conversation not found")
        touch_conversation(db, conversation_id, client_id)
