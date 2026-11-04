"""查询是否学过某个主题，或读取最近学习内容。"""

from memory.learning_memory import get_recent_learning
from memory.memory_manager import find_memory
from tools.log_tool import logger
from errors import make_error


def search_learning_memory(platform=None, topic=None):
    """只读搜索；不创建或修改学习记录。"""
    if platform not in (None, "google_ads", "meta_ads", "cross_platform"):
        return make_error("Validation Error", "无效的平台")
    if topic is not None and (not isinstance(topic, str) or not topic.strip()):
        return make_error("Validation Error", "无效的主题")
    try:
        if topic is None:
            recent = get_recent_learning(10, platform)
            logger.info("Memory Search：最近学习 platform=%s count=%s", platform, len(recent))
            return {"success": True, "topic": "最近学习", "found": bool(recent), "recent_learning": recent}
        matches = find_memory(platform, topic=topic.strip())
        return {"success": True, "topic": "学习记录查询", "query": {"platform": platform, "topic": topic},
                "found": bool(matches), "matches": matches,
                "message": "已找到学习记录" if matches else "没有找到该主题的学习记录"}
    except (OSError, ValueError, KeyError, TypeError) as error:
        logger.error("Memory Search：失败 %s", type(error).__name__)
        return make_error("Memory Read Failed", "无法搜索学习记录")
