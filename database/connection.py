"""数据库连接只读取环境变量；不记录连接串。"""

import os
import psycopg
from psycopg.rows import dict_row


def configured():
    return bool(os.getenv("DATABASE_URL"))


def connect():
    if not configured():
        raise RuntimeError("Database Not Configured")
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5, row_factory=dict_row)


def connected():
    if not configured():
        return False
    try:
        with connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception:
        return False
