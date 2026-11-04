"""为学习 Agent 和各工具共用的日志记录器。"""

import logging
from pathlib import Path


# 日志写入项目的 logs 目录，文件以追加模式保存。
LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "app.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("ads_learning_agent")
logger.setLevel(logging.INFO)
logger.propagate = False


def safe_tool_name(value):
    """日志中只保留规范工具名，避免模型字符串夹带账户信息。"""
    if isinstance(value, str) and len(value) <= 80 and all(char.isascii() and (char.isalnum() or char == "_") for char in value):
        return value
    return "unknown"
if not logger.handlers:
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
