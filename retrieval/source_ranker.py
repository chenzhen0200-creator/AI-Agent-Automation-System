"""用可解释的规则给候选资料排序。"""

import re
from datetime import datetime, timezone


def _tokens(text):
    return set(re.findall(r"[a-z0-9+]+|[\u4e00-\u9fff]", str(text).lower()))


def _match_score(query, text):
    wanted = _tokens(query)
    return len(wanted & _tokens(text)) / len(wanted) if wanted else 0.0


def _freshness(value):
    if not value:
        return 0.3  # 未知更新时间不冒充最新。
    try:
        date = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        days = max(0, (datetime.now(timezone.utc) - date).days)
        return 1.0 if days <= 90 else 0.7 if days <= 365 else 0.3
    except ValueError:
        return 0.3


def rank_sources(sources, query, platform):
    """官方站点始终排在第三方前面，同类来源再按相关度排序。"""
    ranked = []
    for source in sources:
        official = 1.0 if source["source_type"] == "official" else 0.0
        title = _match_score(query, source.get("title", ""))
        relevance = _match_score(query, f"{source.get('title', '')} {source.get('snippet', '')}")
        freshness = _freshness(source.get("published_at"))
        platform_words = ("google",) if platform == "google_ads" else ("meta", "facebook", "instagram") if platform == "meta_ads" else ("google", "meta", "facebook")
        platform_score = 1.0 if any(word in f"{source.get('title', '')} {source.get('snippet', '')} {source.get('url', '')}".lower() for word in platform_words) else 0.0
        score = round(.35 * official + .30 * relevance + .15 * freshness + .15 * title + .05 * platform_score, 3)
        ranked.append({**source, "source_score": {"official_score": official, "relevance_score": round(relevance, 3),
                                              "freshness_score": freshness, "title_score": round(title, 3),
                                              "platform_score": platform_score, "final_score": score}})
    return sorted(ranked, key=lambda item: (item["source_type"] == "official", item["source_score"]["final_score"]), reverse=True)
