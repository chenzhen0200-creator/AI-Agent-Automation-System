"""广告学习领域的长期记忆接口。"""

from memory.memory_manager import MemoryReadError, MemoryWriteError, add_memory, find_memory, list_recent_memory, load_memory
from errors import make_error
from tools.log_tool import logger


def record_learning(platform, category, topic):
    """成功学习一个明确主题后创建或更新长期记录。"""
    if not isinstance(topic, str) or not topic.strip():
        return make_error("Validation Error", "学习主题不能为空")
    try:
        record = add_memory(platform, category, topic.strip())
        return {"success": True, "memory": record}
    except MemoryReadError:
        return make_error("Memory Read Failed", "无法读取学习记录，进度未保存")
    except (MemoryWriteError, OSError, ValueError, KeyError, TypeError) as error:
        logger.error("error_type=Memory Write Failed exception_type=%s", type(error).__name__)
        return make_error("Memory Write Failed", "学习进度保存失败")


def get_learning_history(platform=None):
    """返回指定平台或全部平台的主题记录。"""
    data = load_memory()
    if platform is None:
        return {name: data[name] for name in ("google_ads", "meta_ads", "cross_platform")}
    if platform not in ("google_ads", "meta_ads", "cross_platform"):
        raise ValueError("无效的平台")
    return data[platform]


def get_topic_memory(platform, category, topic):
    """按平台、类别和主题取回已学记录。"""
    return next((item for item in find_memory(platform, category, topic)
                 if item["topic"].casefold() == topic.casefold()), None)


def get_recent_learning(limit=10, platform=None):
    """返回最近的学习事件，包括重复学习。"""
    return list_recent_memory(limit, platform)


def get_learning_statistics():
    """返回去重后的主题数量。"""
    return load_memory()["statistics"]
