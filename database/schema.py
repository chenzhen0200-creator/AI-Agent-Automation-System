"""仅建立缺失的表；从不删除或重建已有表。"""

from threading import Lock
from database.connection import connect

_ready = False
_lock = Lock()


def ensure_schema():
    global _ready
    if _ready:
        return
    with _lock:
        if _ready:
            return
        with connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY, client_id VARCHAR(64) NOT NULL,
                title VARCHAR(100) NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
            db.execute("""CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY, conversation_id UUID NOT NULL
                    REFERENCES conversations(id) ON DELETE CASCADE,
                role VARCHAR(16) NOT NULL, content TEXT NOT NULL,
                platform VARCHAR(32), intent VARCHAR(32), execution_mode VARCHAR(32),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
            db.execute("CREATE INDEX IF NOT EXISTS conversations_client_updated_idx ON conversations(client_id, updated_at DESC)")
            db.execute("CREATE INDEX IF NOT EXISTS messages_conversation_created_idx ON messages(conversation_id, created_at)")
        _ready = True
