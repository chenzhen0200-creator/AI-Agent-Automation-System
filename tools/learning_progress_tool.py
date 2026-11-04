"""根据长期 Learning Memory 动态生成学习进度。"""

from memory.learning_memory import get_learning_history, get_learning_statistics, get_recent_learning
from tools.log_tool import logger
from errors import make_error


def _platform_progress(platform, history):
    concepts = list(history["concepts"])
    steps = list(history["steps"])
    cases = list(history["analysis"])
    count = len(concepts) + len(steps) + len(cases)
    label = "Google Ads" if platform == "google_ads" else "Meta Ads"
    recent = get_recent_learning(1, platform)
    if not concepts:
        next_topic = f"学习 {label} 的 CTR 概念"
    elif not steps:
        next_topic = f"学习 {label} 的广告系列图文步骤"
    elif not cases:
        next_topic = f"学习 {label} 的一个指标异常案例"
    else:
        next_topic = f"继续学习 {label} 的新主题"
    return {
        "learned_concepts": concepts,
        "learned_steps": steps,
        "learned_case_analyses": cases,
        "concept_count": len(concepts), "step_count": len(steps), "analysis_count": len(cases),
        "completed_topic_count": count,
        "current_stage": "未开始" if count == 0 else "入门" if count < 3 else "练习" if count < 8 else "进阶",
        "recent_topic": recent[0]["topic"] if recent else None,
        "recommended_next": next_topic,
    }


def get_learning_progress(_user_goal=None):
    """从 Learning Memory 读取两个平台的实时学习摘要。"""
    try:
        history = get_learning_history()
        statistics = get_learning_statistics()
        progress = {name: _platform_progress(name, history[name]) for name in ("google_ads", "meta_ads")}
        recent = get_recent_learning(1)
        return {"success": True, "topic": "学习进度", "progress": progress,
                "recent_topic": recent[0]["topic"] if recent else None,
                "total_topics": statistics["total_topics"], "statistics": statistics}
    except (OSError, ValueError, KeyError, TypeError) as error:
        logger.error("Memory Read：进度生成失败 %s", type(error).__name__)
        return make_error("Memory Read Failed", "无法读取学习进度")
