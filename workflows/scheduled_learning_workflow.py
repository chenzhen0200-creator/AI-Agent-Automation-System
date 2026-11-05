"""按需检索官方资料，作为未来定时学习的基础。"""

from errors import make_error


def run_scheduled_learning(context, run_tool):
    inputs = context["inputs"]
    platform = inputs.get("platform", "google_ads")
    if platform not in ("google_ads", "meta_ads"):
        return make_error("Validation Error", "platform 只能是 google_ads 或 meta_ads")
    default_query = "Google Ads official latest updates" if platform == "google_ads" else "Meta Ads official latest updates"
    query = inputs.get("query", default_query)
    if not isinstance(query, str) or not query.strip() or len(query) > 500:
        return make_error("Validation Error", "query 必须是 1 到 500 字符的文字")
    context["execution_trace"].append("official_knowledge_search")
    search = run_tool("search_ads_knowledge", {
        "platform": platform, "query": query, "official_only": True,
        "freshness_required": True,
    })
    if not search["success"]:
        if search.get("error_type") not in {
                "Search API Not Configured", "Search Request Failed", "No Search Results",
                "Official Source Not Found", "Content Extraction Failed"}:
            return search
        # 只提供稳定概念学习，不宣称已取得最新官方资料。
        context["warnings"].append({"error_type": search["error_type"],
                                    "message": "最新官方资料未核实；以下仅为基础概念学习"})
        context["fallback_used"] = "stable_tool"
        context["execution_trace"].append("stable_concept_fallback")
        concept_name = "explain_google_ads_concept" if platform == "google_ads" else "explain_meta_ads_concept"
        concept_query = "Google Ads CTR 是什么" if platform == "google_ads" else "Meta Ads Pixel 是什么"
        concept = run_tool(concept_name, {"topic": concept_query})
        if not concept["success"]:
            return concept
        return {"success": True, "platform": platform, "summary": concept.get("explanation", ""),
                "topic": concept.get("topic"), "sources": [], "freshness_unverified": True}
    sources = search.get("sources", [])
    excerpts = [item.get("content", "")[:300] for item in search.get("retrieved_content", [])[:3]]
    context["execution_trace"].append("learning_summary")
    return {"success": True, "platform": platform, "summary": "\n".join(excerpts), "sources": sources}
