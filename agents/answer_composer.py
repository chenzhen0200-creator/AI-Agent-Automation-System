"""把已执行工具的结构化结果整理为可读答案，不生成未经验证的事实。"""


def _list_lines(label, values, limit=4):
    if not isinstance(values, list) or not values:
        return []
    return [label + "："] + [f"- {item}" for item in values[:limit] if isinstance(item, str)]


def _render(tool_name, result):
    if tool_name == "analyze_ads_screenshot":
        return result.get("screenshot_guidance", "已取得截图分析结果。")
    if tool_name in ("get_google_ads_steps", "get_meta_ads_steps"):
        lines = [f"{result.get('topic', '操作')}："]
        for step in result.get("steps", [])[:6]:
            lines.append(f"{step['step_number']}. {step['title']}：{step['action']}；预计进入{step['next_page']}。")
        return "\n".join(lines)
    if tool_name in ("explain_google_ads_concept", "explain_meta_ads_concept"):
        if "explanation" not in result:
            return f"可学习主题：{', '.join(result.get('available_topics', [])[:12])}"
        lines = [f"{result.get('topic', '概念')}：{result['explanation']}"]
        if result.get("formula"):
            lines.append(f"公式：{result['formula']}")
        if result.get("example"):
            lines.append(f"例子：{result['example']}")
        return "\n".join(lines)
    if tool_name in ("analyze_google_ads_case", "analyze_meta_ads_case"):
        if "issue" not in result:
            return f"可分析问题：{', '.join(result.get('available_issues', [])[:12])}"
        lines = [f"案例：{result['issue']}"]
        lines += _list_lines("可能原因", result.get("possible_causes"))
        lines += _list_lines("建议检查", result.get("checks"))
        lines += _list_lines("学习建议", result.get("recommended_actions"))
        return "\n".join(lines)
    if tool_name == "search_ads_knowledge":
        sources = result.get("sources", [])
        if not sources:
            return "检索没有返回可引用来源。"
        lines = ["检索到以下有出处的资料；请结合来源核对当前规则："]
        for source in sources[:3]:
            date = source.get("updated_at") or "更新时间未知"
            lines.append(f"- {source.get('title', '未命名页面')}（{source.get('source_type', 'unknown')}，{date}）：{source['url']}")
        for item in result.get("retrieved_content", [])[:2]:
            if item.get("content"):
                lines.append(f"相关段落（{item['source_url']}）：{item['content'][:500]}")
        return "\n".join(lines)
    if tool_name == "search_learning_memory":
        if result.get("recent_learning") is not None:
            recent = result["recent_learning"]
            return "最近学习：" + ("、".join(item.get("topic", "") for item in recent[:5]) if recent else "暂无记录")
        matches = result.get("matches", [])
        return "已学过：" + "、".join(item.get("topic", "") for item in matches[:5]) if matches else "没有找到该主题的学习记录。"
    if tool_name == "get_learning_progress":
        progress = result.get("progress", {})
        lines = [f"共完成 {result.get('total_topics', 0)} 个主题。"]
        for name, label in (("google_ads", "Google Ads"), ("meta_ads", "Meta Ads")):
            item = progress.get(name, {})
            lines.append(f"{label}：{item.get('completed_topic_count', 0)} 个主题，阶段：{item.get('current_stage', '未知')}。下一步：{item.get('recommended_next', '待定')}")
        return "\n".join(lines)
    if tool_name == "compare_google_meta":
        if "key_difference" not in result:
            return f"可比较主题：{', '.join(result.get('available_topics', [])[:10])}"
        return f"{result.get('topic', '平台对比')}：{result['key_difference']}\n适用建议：{result.get('when_to_use_each', '')}"
    return "工具已返回结构化结果。"


def compose_answer(context):
    """仅使用本次成功工具或真实模型直接答案；警告显式展示。"""
    if context.get("direct_answer") is not None:
        answer = context["direct_answer"]
    else:
        sections = [_render(item["tool_name"], item["result"])
                    for item in context["tool_results"] if item["success"]]
        answer = "\n\n".join(section for section in sections if section)
    warnings = context.get("warnings", [])
    if warnings:
        answer += "\n\n提示：" + "；".join(item.get("message", str(item)) if isinstance(item, dict) else str(item)
                                          for item in warnings)
    return answer or "没有取得可用的教学内容。"
