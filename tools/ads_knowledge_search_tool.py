"""从外部搜索中挑选有出处的广告学习资料。"""

from retrieval.content_extractor import extract_content
from retrieval.source_filter import filter_sources
from retrieval.source_ranker import rank_sources
from retrieval.web_search_client import search_web
from errors import make_error


def search_ads_knowledge(platform, query, official_only=True, freshness_required=True):
    """只读检索；无搜索密钥或无可用来源时返回结构化错误。"""
    if platform not in ("google_ads", "meta_ads", "cross_platform") or not isinstance(query, str) or not query.strip():
        return make_error("Validation Error", "平台或搜索问题无效")
    if not isinstance(official_only, bool) or not isinstance(freshness_required, bool):
        return make_error("Validation Error", "检索选项必须为布尔值")
    search = search_web(query, platform, freshness_required=freshness_required)
    if not search["success"]:
        return search
    if not search["results"]:
        return make_error("No Search Results", "未找到相关搜索结果", retry_count=search["retry_count"])
    candidates = filter_sources(search["results"], platform, official_only=False)
    if not candidates:
        return make_error("Source Rejected", "搜索结果均未通过来源筛选", retry_count=search["retry_count"])
    official = [item for item in candidates if item["source_type"] == "official"]
    if official_only and not official:
        return make_error("Official Source Not Found", "未找到可用的官方来源", retry_count=search["retry_count"])
    # 即使允许第三方，也只在官方结果不足时使用已审核的第三方来源。
    retrieved = []
    sources = []
    groups = [official]
    if not official_only:
        groups.append([item for item in candidates if item["source_type"] == "third_party"])
    for group in groups:
        for item in rank_sources(group, query, platform)[:5]:
            extracted = extract_content(item, query, platform)
            if not extracted["success"]:
                continue
            sources.append({"title": extracted["title"], "url": item["url"], "source_type": item["source_type"],
                            "updated_at": extracted["updated_at"], "relevance": item["source_score"]["relevance_score"],
                            "source_score": item["source_score"]})
            retrieved.append({"source_url": item["url"], "content": extracted["content"],
                              "relevant_sections": extracted["relevant_sections"]})
        if retrieved:
            break  # 官方页面可提取时，不使用第三方内容。
    if not retrieved:
        return make_error("Content Extraction Failed", "找到来源，但无法提取相关正文", retry_count=search["retry_count"])
    return {"success": True, "platform": platform, "query": query, "freshness_required": freshness_required,
            "retry_count": search["retry_count"],
            "sources": sources, "retrieved_content": retrieved}
