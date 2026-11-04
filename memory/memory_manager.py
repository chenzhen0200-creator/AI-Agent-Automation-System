"""统一管理本地学习记忆 JSON 的读、写、更新与搜索。"""

import json
from datetime import datetime
from pathlib import Path

from tools.log_tool import logger


MEMORY_PATH = Path(__file__).resolve().parent.parent / "data" / "learning_memory.json"
CATEGORIES = {"concept": "concepts", "steps": "steps", "analysis": "analysis", "comparison": "comparison"}


class MemoryReadError(OSError):
    """本地学习记录无法读取或解析。"""


class MemoryWriteError(OSError):
    """本地学习记录无法安全写入。"""


def _empty_memory():
    return {
        "google_ads": {"concepts": {}, "steps": {}, "analysis": {}},
        "meta_ads": {"concepts": {}, "steps": {}, "analysis": {}},
        "cross_platform": {"comparison": {}},
        "recent_learning": [],
        "statistics": {"total_topics": 0, "google_ads_topics": 0, "meta_ads_topics": 0, "cross_platform_topics": 0},
    }


def _bucket(data, platform, category):
    if platform not in ("google_ads", "meta_ads", "cross_platform"):
        raise ValueError("无效的平台")
    if category not in CATEGORIES or (platform == "cross_platform") != (category == "comparison"):
        raise ValueError("无效的学习类别")
    return data[platform][CATEGORIES[category]]


def _refresh_statistics(data):
    counts = {name: sum(len(items) for items in data[name].values()) for name in ("google_ads", "meta_ads", "cross_platform")}
    data["statistics"] = {
        "total_topics": sum(counts.values()),
        "google_ads_topics": counts["google_ads"],
        "meta_ads_topics": counts["meta_ads"],
        "cross_platform_topics": counts["cross_platform"],
    }


def load_memory():
    """读取并检查文件结构；缺失时返回空结构，不覆盖损坏文件。"""
    try:
        if not MEMORY_PATH.exists():
            logger.info("Memory Read：尚无文件，使用空记忆")
            return _empty_memory()
        data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("学习记忆文件格式不正确")
        for platform, categories in _empty_memory().items():
            if platform in ("recent_learning", "statistics"):
                continue
            if not isinstance(data.get(platform), dict) or not all(isinstance(data[platform].get(key), dict) for key in categories):
                raise ValueError("学习记忆文件格式不正确")
        if not isinstance(data.get("recent_learning"), list):
            raise ValueError("最近学习记录格式不正确")
        _refresh_statistics(data)
    except (OSError, ValueError, KeyError, TypeError) as error:
        logger.error("error_type=Memory Read Failed exception_type=%s", type(error).__name__)
        raise MemoryReadError("学习记录读取失败") from error
    logger.info("Memory Read：%s", MEMORY_PATH.name)
    return data


def save_memory(data):
    """使用临时文件原子替换，避免部分写入。"""
    try:
        _refresh_statistics(data)
        temporary = MEMORY_PATH.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(MEMORY_PATH)
    except (OSError, ValueError, KeyError, TypeError) as error:
        logger.error("error_type=Memory Write Failed exception_type=%s", type(error).__name__)
        raise MemoryWriteError("学习记录保存失败") from error
    logger.info("Memory Write：%s", MEMORY_PATH.name)


def add_memory(platform, category, topic):
    """新主题创建记录；已有主题转为更新，不创建重复项。"""
    data = load_memory()
    bucket = _bucket(data, platform, category)
    if topic in bucket:
        return update_memory(platform, category, topic)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    record = {"topic": topic, "category": category, "platform": platform,
              "first_learned_at": now, "last_learned_at": now, "learn_count": 1, "status": "learned"}
    bucket[topic] = record
    data["recent_learning"].append({"platform": platform, "category": category, "topic": topic, "learned_at": now})
    data["recent_learning"] = data["recent_learning"][-50:]
    save_memory(data)
    logger.info("Memory Write：platform=%s category=%s", platform, category)
    return record


def update_memory(platform, category, topic, status="learned"):
    """重复学习时只增加次数，保留首次学习时间。"""
    data = load_memory()
    bucket = _bucket(data, platform, category)
    if topic not in bucket:
        raise KeyError("主题尚未记录")
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    record = bucket[topic]
    record["learn_count"] += 1
    record["last_learned_at"] = now
    record["status"] = status
    data["recent_learning"].append({"platform": platform, "category": category, "topic": topic, "learned_at": now})
    data["recent_learning"] = data["recent_learning"][-50:]
    save_memory(data)
    logger.info("Memory Update：platform=%s category=%s count=%s", platform, category, record["learn_count"])
    return record


def find_memory(platform=None, category=None, topic=None):
    """按平台、类别和主题搜索；主题支持大小写不敏感的包含匹配。"""
    data = load_memory()
    platforms = (platform,) if platform else ("google_ads", "meta_ads", "cross_platform")
    found = []
    for name in platforms:
        if name not in ("google_ads", "meta_ads", "cross_platform"):
            raise ValueError("无效的平台")
        for bucket_name, items in data[name].items():
            if category and bucket_name != CATEGORIES.get(category):
                continue
            found.extend(record for key, record in items.items()
                         if topic is None or topic.casefold() in key.casefold() or key.casefold() in topic.casefold())
    logger.info("Memory Search：platform=%s category=%s matches=%s", platform, category, len(found))
    return found


def delete_memory(platform, category, topic):
    """仅提供显式调用的删除接口；Agent 不暴露此函数为 Tool。"""
    data = load_memory()
    removed = _bucket(data, platform, category).pop(topic, None)
    if removed is not None:
        data["recent_learning"] = [item for item in data["recent_learning"]
                                   if not (item["platform"] == platform and item["category"] == category and item["topic"] == topic)]
        save_memory(data)
        logger.info("Memory Update：删除 platform=%s category=%s", platform, category)
    return removed is not None


def list_recent_memory(limit=10, platform=None):
    """从最近学习历史中按时间倒序返回。"""
    data = load_memory()
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("limit 必须是正整数")
    items = data["recent_learning"]
    if platform:
        items = [item for item in items if item.get("platform") == platform]
    logger.info("Memory Read：最近记录 platform=%s limit=%s", platform, limit)
    return list(reversed(items[-limit:]))


# 短期记忆只在当前 Python 进程中存在，不写入长期 JSON。
SHORT_TERM_CONTEXT = {"current_platform": None, "current_topic": None, "current_intent": None,
                      "last_tool_call": None, "current_step": None}


def update_short_term(**values):
    """更新本次会话的当前上下文。"""
    for key, value in values.items():
        if key in SHORT_TERM_CONTEXT:
            SHORT_TERM_CONTEXT[key] = value
    return dict(SHORT_TERM_CONTEXT)


def get_short_term():
    """读取当前会话上下文的副本。"""
    return dict(SHORT_TERM_CONTEXT)
