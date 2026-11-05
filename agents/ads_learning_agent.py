"""优先尝试模型选择工具；不可用时回退到现有两层规则。"""

from errors import make_error, normalize_error
from agents.answer_composer import compose_answer
from guardrails.permission_guard import check_permission
from guardrails.risk_classifier import classify_risk
from tools.log_tool import logger, safe_tool_name
from tools.tool_registry import execute_tool, get_available_tools
from tools.screenshot_analysis_tool import combine_screenshot_with_steps
from memory.learning_memory import record_learning
from memory.memory_manager import get_short_term, update_short_term
from llm.model_client import choose_action
from llm.tool_schema import get_tool_schemas
from llm.tool_validation import validate_tool_call


def detect_platform(goal):
    """第一层：识别 Google、Meta、跨平台或未知。"""
    text = goal.lower()
    google = any(word in text for word in ("google", "谷歌", "youtube", "search", "pmax", "performance max", "demand gen", "shopping"))
    import re
    meta = any(word in text for word in ("meta", "facebook", "instagram", "脸书", "pixel", "capi", "ad set", "advantage+")) or bool(re.search(r"(?<![a-z])(?:fb|ig)(?![a-z])", text))
    # “广告组”在两个平台都存在；没有明确 Google 标识时按常见 Meta 提问处理。
    if "广告组" in text and not google:
        meta = True
    comparison = any(word in text for word in ("区别", "对比", "比较", " vs ", "不同", "差异"))
    generic_pair = any(word in text for word in ("两个平台", "两平台", "跨平台"))
    if (google and meta) or (comparison and (google or meta or generic_pair)):
        return "cross_platform"
    if google:
        return "google_ads"
    if meta:
        return "meta_ads"
    # 未指定平台的学习进度，默认查看两个平台。
    if any(word in text for word in ("学习进度", "学到哪里", "学习记录")):
        return "cross_platform"
    if any(word in text for word in ("学过", "之前学", "上次学", "最近学", "记得吗")):
        return "cross_platform"
    return "unknown"


def detect_intent(goal):
    """第二层：识别学习意图。"""
    text = goal.lower()
    if any(word in text for word in ("学过吗", "学过没有", "之前学过", "之前学", "上次学", "最近学", "记得吗")):
        return "memory"
    if any(word in text for word in ("学习进度", "学到哪里", "学习记录")):
        return "progress"
    # 易变化的平台规则、功能与界面，应先核实外部资料。
    if any(word in text for word in ("现在", "最新", "官方", "目前", "2026", "最近更新", "当前规则", "新功能")):
        return "retrieval"
    if any(word in text for word in ("区别", "对比", "比较", " vs ", "不同", "差异")):
        return "comparison"
    if any(word in text for word in ("google", "谷歌")) and any(word in text for word in ("meta", "facebook", "instagram")):
        return "comparison"
    # 界面定位问题优先交给图文步骤工具。
    if any(word in text for word in ("在哪里", "哪里", "按钮", "怎么添加", "添加", "复制", "duplicate", "copy", "教我")):
        return "steps"
    if any(word in text for word in ("为什么", "异常", "偏高", "偏低", "太高", "太低", "下降", "花不出去", "疲劳", "过窄", "高但", "低但", "分析", "案例", "高", "低", "learning limited", "addtocart", "搜索词不相关", "表现差", "点击多")):
        return "analysis"
    if any(word in text for word in ("怎么", "如何", "步骤", "创建", "设置", "配置", "投放")):
        return "steps"
    if any(word in text for word in ("是什么", "什么意思", "解释", "含义", "概念")):
        return "concept"
    return "unknown"


ROUTES = {
    ("google_ads", "concept"): "explain_google_ads_concept",
    ("google_ads", "steps"): "get_google_ads_steps",
    ("google_ads", "analysis"): "analyze_google_ads_case",
    ("meta_ads", "concept"): "explain_meta_ads_concept",
    ("meta_ads", "steps"): "get_meta_ads_steps",
    ("meta_ads", "analysis"): "analyze_meta_ads_case",
    ("cross_platform", "comparison"): "compare_google_meta",
    ("cross_platform", "progress"): "get_learning_progress",
    ("google_ads", "progress"): "get_learning_progress",
    ("meta_ads", "progress"): "get_learning_progress",
    ("cross_platform", "memory"): "search_learning_memory",
    ("google_ads", "memory"): "search_learning_memory",
    ("meta_ads", "memory"): "search_learning_memory",
    ("google_ads", "retrieval"): "search_ads_knowledge",
    ("meta_ads", "retrieval"): "search_ads_knowledge",
    ("cross_platform", "retrieval"): "search_ads_knowledge",
}


MAX_TOOL_STEPS = 3
LEARNING_INTENTS = {"concept", "steps", "analysis", "comparison"}
SEARCH_FAILURES = {
    "Search API Not Configured", "Search Request Failed", "No Search Results",
    "Official Source Not Found", "Content Extraction Failed",
}
VISION_FAILURES = {"Vision Not Configured", "Vision Request Failed"}
BLOCKING_FAILURES = {
    "High Risk Action Blocked", "Permission Denied", "Invalid Tool Call",
    "Validation Error", "Tool Not Found", "Max Tool Steps Exceeded",
}


def _new_context(user_message, image_path):
    """本次执行的唯一上下文；不写入日志或长期文件。"""
    return {
        "user_message": user_message, "platform": detect_platform(user_message),
        "intent": detect_intent(user_message), "image_path": image_path,
        "current_tool": None, "tool_results": [], "memory_context": None,
        "retrieval_context": None, "vision_context": None, "step_count": 0,
        "execution_mode": "rule_fallback", "execution_trace": [],
        "memory_saved": None, "sources": [], "warnings": [],
        "fallback_used": "none", "risk_level": "low", "retry_count": 0,
        "llm_retry_count": 0, "direct_answer": None,
        "freshness_unverified": False, "screenshot_unverified": False,
    }


def _safe_error(context, error):
    """所有失败都保留已发生的步骤和可恢复建议。"""
    failure = normalize_error(error)
    if not context["execution_trace"] or context["execution_trace"][-1] != "safe_error":
        context["execution_trace"].append("safe_error")
    failure.update({
        "execution_mode": context["execution_mode"], "platform": context["platform"],
        "intent": context["intent"], "answer": failure["message"] + "。" + failure["suggested_action"],
        "tool_results": context["tool_results"], "memory_saved": context["memory_saved"],
        "sources": context["sources"], "warnings": context["warnings"],
        "execution_trace": list(context["execution_trace"]),
        "step_count": context["step_count"], "fallback_used": context["fallback_used"],
        "risk_level": failure.get("risk_level", context["risk_level"]),
        "retry_count": context["retry_count"],
    })
    logger.warning(
        "error_type=%s tool_name=%s recoverable=%s retry_count=%s fallback_used=%s risk_level=%s blocked_action=%s",
        failure["error_type"], safe_tool_name(context["current_tool"]) if context["current_tool"] else "none",
        failure["recoverable"], context["retry_count"], context["fallback_used"],
        failure["risk_level"], failure.get("blocked_action"),
    )
    return failure


def _warning(context, error, message=None):
    normalized = normalize_error(error)
    context["warnings"].append({
        "error_type": normalized["error_type"],
        "message": message or normalized["message"],
        "recoverable": normalized["recoverable"],
        "suggested_action": normalized["suggested_action"],
    })


def _tool_info(tool_name):
    return next((tool for tool in get_available_tools() if tool["name"] == tool_name), None)


def _arguments_for(context, tool_name, topic=None):
    """规则路径只生成注册 Schema 允许的参数。"""
    meta = _tool_info(tool_name)
    if meta is None:
        return {}
    message = context["user_message"] if topic is None else topic
    intent = meta["intent"]
    if intent == "memory":
        recent = any(word in context["user_message"] for word in ("上次学", "最近学"))
        short_term = get_short_term()
        refers_to_current = any(word in context["user_message"] for word in ("这个", "它", "刚才"))
        topic = short_term["current_topic"] if refers_to_current and short_term["current_topic"] else context["user_message"]
        platform = context["platform"]
        if refers_to_current and short_term["current_platform"] in ("google_ads", "meta_ads"):
            platform = short_term["current_platform"]
        return {"platform": None if platform == "cross_platform" else platform,
                "topic": None if recent else topic}
    if intent == "retrieval":
        return {"platform": context["platform"], "query": context["user_message"],
                "official_only": True, "freshness_required": True}
    if intent == "progress":
        return {}
    if intent == "screenshot":
        hint = context["platform"] if context["platform"] in ("google_ads", "meta_ads") else "unknown"
        return {"image_path": context["image_path"], "user_goal": context["user_message"], "platform_hint": hint}
    argument_name = "issue" if intent == "analysis" else "topic"
    return {argument_name: message}


def _invoke(context, tool_name, arguments, internal=None):
    """每次工具调用都计数，并依次经过校验、风险和权限检查。"""
    context["current_tool"] = tool_name
    if context["step_count"] >= MAX_TOOL_STEPS:
        return make_error("Max Tool Steps Exceeded", "本次任务调用工具次数已达到上限",
                          suggested_action="请将问题拆分后继续")
    context["execution_trace"].append("validation")
    if _tool_info(tool_name) is None:
        context["execution_trace"].append("risk_classifier")
        permission = check_permission(tool_name, context["user_message"], arguments,
                                      {tool["name"] for tool in get_available_tools()})
        return normalize_error(permission)
    validation = validate_tool_call(tool_name, arguments)
    if not validation["success"]:
        return validation
    context["execution_trace"].append("risk_classifier")
    risk = classify_risk(tool_name, context["user_message"], arguments)
    if risk["risk_level"] == "high":
        context["execution_trace"].append("permission_guard")
        return check_permission(tool_name, context["user_message"], arguments,
                                {tool["name"] for tool in get_available_tools()})
    if risk["risk_level"] == "medium":
        context["risk_level"] = "medium"
    context["execution_trace"].append("permission_guard")
    permission = check_permission(tool_name, context["user_message"], arguments,
                                  {tool["name"] for tool in get_available_tools()})
    if not permission["success"]:
        return permission
    context["step_count"] += 1
    context["execution_trace"].append("tool_execution:" + tool_name)
    options = internal if isinstance(internal, dict) else {}
    # 旧教学 Tool 用 user_goal 作为位置参数；对外 Schema 保持 topic / issue。
    legacy_argument = ("topic" if "topic" in arguments else "issue" if "issue" in arguments else None
                       ) if _tool_info(tool_name)["intent"] in LEARNING_INTENTS else None
    handler_args = (arguments[legacy_argument],) if legacy_argument else ()
    handler_kwargs = {key: value for key, value in arguments.items() if key != legacy_argument}
    result = execute_tool(
        tool_name, *handler_args,
        policy_context={"user_goal": context["user_message"], "arguments": arguments,
                        "fallback_used": context["fallback_used"]},
        **handler_kwargs, **options,
    )
    if not isinstance(result, dict):
        result = make_error("Tool Execution Error", "工具未返回有效结构")
    context["retry_count"] += result.get("retry_count", 0)
    context["tool_results"].append({
        "tool_name": tool_name, "success": result.get("success") is True,
        "result": {key: value for key, value in result.items() if key != "success"},
    })
    if result.get("success"):
        if tool_name == "search_ads_knowledge":
            context["retrieval_context"] = result
            context["sources"].extend(result.get("sources", []))
        elif tool_name == "analyze_ads_screenshot":
            context["vision_context"] = result
            context["platform"] = result.get("platform", context["platform"])
        elif tool_name == "search_learning_memory":
            context["memory_context"] = result
    return result


def _save_learning(context):
    """只有组成可返回答案的成功学习工具才写长期 Memory。"""
    seen = set()
    successful = [item for item in context["tool_results"] if item["success"]]
    for item in successful:
        meta = _tool_info(item["tool_name"])
        if meta is None or meta["intent"] not in LEARNING_INTENTS:
            continue
        topic = item["result"].get("topic")
        if not isinstance(topic, str) or topic.endswith("目录"):
            continue
        platform = meta["platform"]
        key = (platform, meta["intent"], topic)
        if key in seen:
            continue
        seen.add(key)
        context["execution_trace"].append("memory_write")
        saved = record_learning(platform, meta["intent"], topic)
        context["memory_saved"] = (context["memory_saved"] is not False and saved["success"])
        if not saved["success"]:
            _warning(context, saved, "学习内容已返回，但进度未保存")
            logger.warning(
                "error_type=%s tool_name=%s recoverable=%s retry_count=0 fallback_used=%s risk_level=%s blocked_action=none",
                saved["error_type"], safe_tool_name(item["tool_name"]), saved["recoverable"],
                context["fallback_used"], context["risk_level"],
            )
    if successful:
        last = successful[-1]
        learning_result = next((item for item in reversed(successful)
                                if (_tool_info(item["tool_name"]) or {}).get("intent") in LEARNING_INTENTS), None)
        try:
            update_short_term(
                current_platform=context["platform"],
                current_topic=(learning_result["result"].get("topic") if learning_result
                               else get_short_term()["current_topic"]),
                current_intent=context["intent"], last_tool_call=last["tool_name"],
                current_step=1 if context["intent"] == "steps" else None,
            )
        except Exception as error:
            context["memory_saved"] = False
            _warning(context, make_error("Memory Write Failed", "当前会话上下文未能保存"))
            logger.error("error_type=Memory Write Failed exception_type=%s", type(error).__name__)


def _complete(context):
    """统一生成面向用户的答案、来源、警告和执行轨迹。"""
    if context["direct_answer"] is None and not any(item["success"] for item in context["tool_results"]):
        return _safe_error(context, make_error("Tool Execution Error", "没有取得可用的教学内容"))
    context["execution_trace"].append("answer_composition")
    preliminary = compose_answer(context)
    if not preliminary or preliminary == "没有取得可用的教学内容。":
        return _safe_error(context, make_error("Tool Execution Error", "无法整理工具结果"))
    _save_learning(context)
    return {
        "success": True, "execution_mode": context["execution_mode"],
        "platform": context["platform"], "intent": context["intent"],
        "answer": compose_answer(context), "tool_results": context["tool_results"],
        "memory_saved": context["memory_saved"], "sources": context["sources"],
        "warnings": context["warnings"], "execution_trace": list(context["execution_trace"]),
        "step_count": context["step_count"], "fallback_used": context["fallback_used"],
        "risk_level": context["risk_level"], "retry_count": context["retry_count"],
        "llm_retry_count": context["llm_retry_count"],
        "freshness_unverified": context["freshness_unverified"],
        "screenshot_unverified": context["screenshot_unverified"],
    }


def _needs_steps(message):
    text = message.lower()
    return any(word in text for word in ("怎么", "如何", "设置", "步骤", "哪里", "按钮", "添加", "创建", "下一步", "点哪个"))


def _needs_analysis(message):
    text = message.lower()
    return any(word in text for word in ("为什么", "异常", "偏高", "偏低", "下降", "表现差", "转化低", "花不出去", "分析", "排查"))


def _stable_tool(context):
    if context["platform"] == "cross_platform":
        return "compare_google_meta"
    if _needs_analysis(context["user_message"]):
        return "analyze_google_ads_case" if context["platform"] == "google_ads" else "analyze_meta_ads_case"
    return "explain_google_ads_concept" if context["platform"] == "google_ads" else "explain_meta_ads_concept"


def _run_single(context, tool_name, arguments):
    result = _invoke(context, tool_name, arguments)
    if result["success"]:
        return _complete(context)
    if tool_name == "search_ads_knowledge" and result["error_type"] in SEARCH_FAILURES:
        context["execution_trace"].append("external_search_failed")
        context["execution_trace"].append("stable_tool_fallback")
        context["fallback_used"] = "stable_tool"
        stable_name = _stable_tool(context)
        fallback = _invoke(context, stable_name, _arguments_for(context, stable_name))
        if fallback["success"]:
            context["freshness_unverified"] = True
            _warning(context, result, "未能核实最新官方资料；以下仅为稳定教学内容")
            return _complete(context)
    return _safe_error(context, result)


def _run_screenshot(context, vision_adapter):
    screenshot = _invoke(
        context, "analyze_ads_screenshot", _arguments_for(context, "analyze_ads_screenshot"),
        {"adapter": vision_adapter, "defer_steps": True},
    )
    if not screenshot["success"]:
        if (screenshot["error_type"] in VISION_FAILURES and context["platform"] in ("google_ads", "meta_ads")
                and _needs_steps(context["user_message"])):
            context["execution_trace"].append("vision_failed")
            context["execution_trace"].append("steps_fallback")
            context["fallback_used"] = "steps_tool"
            steps_name = "get_google_ads_steps" if context["platform"] == "google_ads" else "get_meta_ads_steps"
            steps = _invoke(context, steps_name, _arguments_for(context, steps_name))
            if steps["success"]:
                context["intent"] = "steps"
                context["screenshot_unverified"] = True
                _warning(context, screenshot, "未识别截图；以下是通用步骤，不能确认当前页面的按钮")
                return _complete(context)
        return _safe_error(context, screenshot)
    if screenshot.get("steps_requested"):
        context["execution_trace"].append("auxiliary_steps")
        steps_name = "get_google_ads_steps" if context["platform"] == "google_ads" else "get_meta_ads_steps"
        steps = _invoke(context, steps_name, _arguments_for(context, steps_name, screenshot.get("steps_topic_query")))
        if steps["success"]:
            combined = combine_screenshot_with_steps(screenshot, steps)
            context["vision_context"] = combined
            for item in context["tool_results"]:
                if item["tool_name"] == "analyze_ads_screenshot":
                    item["result"] = {key: value for key, value in combined.items() if key != "success"}
                    break
            context["intent"] = "steps"
        elif steps["error_type"] == "Max Tool Steps Exceeded":
            return _safe_error(context, steps)
        else:
            _warning(context, steps, "截图已识别，但标准步骤暂不可用")
    return _complete(context)


def _run_combination(context, names):
    """只允许预定的两工具组合；失败时保留可验证的部分。"""
    errors = []
    for name in names:
        result = _invoke(context, name, _arguments_for(context, name))
        if not result["success"]:
            errors.append(result)
            if result["error_type"] in BLOCKING_FAILURES:
                return _safe_error(context, result)
            if name == "search_ads_knowledge" and result["error_type"] in SEARCH_FAILURES:
                context["freshness_unverified"] = True
                _warning(context, result, "最新官方资料未核实；其他内容仅为通用教学")
            else:
                _warning(context, result, "部分学习资料暂不可用")
    if any(item["success"] for item in context["tool_results"]):
        return _complete(context)
    return _safe_error(context, errors[0] if errors else make_error("Tool Execution Error", "组合工具均未取得结果"))


def _plan(context, primary_name):
    """有限组合由明确的问题类型决定，不让模型自由递归调用工具。"""
    message = context["user_message"]
    platform = context["platform"]
    intent = context["intent"]
    # 明确的步骤问题必须交给结构化 Steps Tool，不能用模型选出的简短概念答案替代。
    if intent == "steps" and platform in ("google_ads", "meta_ads"):
        return [ROUTES[(platform, "steps")]]
    if intent in ("memory", "progress"):
        name = ROUTES.get((platform, intent))
        return [name] if name else []
    if intent == "retrieval" and platform in ("google_ads", "meta_ads"):
        if _needs_analysis(message):
            context["intent"] = "analysis"
            analysis = "analyze_google_ads_case" if platform == "google_ads" else "analyze_meta_ads_case"
            return [analysis, "search_ads_knowledge"]
        if _needs_steps(message):
            context["intent"] = "steps"
            steps = "get_google_ads_steps" if platform == "google_ads" else "get_meta_ads_steps"
            return ["search_ads_knowledge", steps]
        return ["search_ads_knowledge"]
    return [primary_name] if primary_name else []


def run_ads_learning_agent(user_goal, screenshot=None, image_path=None, vision_adapter=None):
    """统一执行链：路由、校验、权限、有限工具组合、Memory 与答案。"""
    message = user_goal.strip() if isinstance(user_goal, str) else ""
    provided_image = image_path if image_path is not None else screenshot
    context = _new_context(message, provided_image)
    context["execution_trace"].append("input_received")
    if provided_image is not None:
        context["execution_trace"].append("image_detected")
    context["execution_trace"].append("risk_classifier")
    risk = classify_risk(user_goal=message)
    if risk["risk_level"] == "high":
        context["execution_mode"] = "not_executed"
        context["risk_level"] = "high"
        context["execution_trace"].append("permission_guard")
        blocked = check_permission("direct_request", message)
        return _safe_error(context, blocked)
    if not message:
        return _safe_error(context, make_error("Validation Error", "请输入学习问题"))
    if provided_image is not None:
        context["execution_mode"] = "vision_tool"
        context["intent"] = "screenshot"
        logger.info("screenshot_received=true")
        return _run_screenshot(context, vision_adapter)

    # 明确的图文教学问题直接使用只读 Steps Tool，避免模型把“怎么创建”误选为真实创建动作。
    if context["intent"] == "steps" and context["platform"] in ("google_ads", "meta_ads"):
        tool_name = ROUTES[(context["platform"], "steps")]
        context["execution_trace"].append("rule_steps_route")
        context["execution_mode"] = "rule_fallback"
        context["fallback_used"] = "rule_steps_route"
        return _run_single(context, tool_name, _arguments_for(context, tool_name))

    context["execution_trace"].append("llm_tool_calling")
    decision = choose_action(message, get_tool_schemas())
    context["llm_retry_count"] = decision.get("retry_count", 0)
    selected_name = None
    selected_arguments = None
    if not decision["success"]:
        if decision["error_type"] not in ("LLM Not Configured", "LLM Request Failed"):
            return _safe_error(context, decision)
        context["execution_trace"].append("llm_tool_calling_failed")
        context["execution_trace"].append("rule_fallback")
        context["execution_mode"] = "rule_fallback"
        context["fallback_used"] = "rule_router"
        reason = decision.get("provider_error_type") or (
            decision.get("message") if decision["error_type"] == "LLM Not Configured" else decision["error_type"]
        )
        logger.warning("LLM unavailable, using rule fallback fallback_reason=%s error_type=%s status_code=%s retry_count=%s",
                       safe_tool_name(reason), decision["error_type"], decision.get("status_code", "none"),
                       context["llm_retry_count"])
    elif decision["type"] == "direct_answer":
        if context["intent"] not in ("memory", "progress", "retrieval", "steps"):
            if context["platform"] == "unknown":
                return _safe_error(context, make_error("Unknown Platform", "当前 Agent 仅支持 Google Ads 和 Meta Ads"))
            context["execution_mode"] = "llm_tool_calling"
            context["direct_answer"] = decision["content"]
            return _complete(context)
        context["execution_trace"].append("direct_answer_overridden")
        context["execution_mode"] = "rule_fallback"
        context["fallback_used"] = "rule_router"
    else:
        context["execution_mode"] = "llm_tool_calling"
        selected_name = decision["tool_name"]
        selected_arguments = decision["arguments"]
        context["current_tool"] = selected_name
        context["execution_trace"].append("llm_tool_validation")
        selected_risk = classify_risk(selected_name, message, selected_arguments)
        if selected_risk["risk_level"] == "high":
            return _safe_error(context, check_permission(selected_name, message, selected_arguments,
                                                         {tool["name"] for tool in get_available_tools()}))
        if selected_name == "analyze_ads_screenshot":
            return _safe_error(context, make_error("Invalid Tool Call", "本次未收到用户截图，不能分析图片"))
        if _tool_info(selected_name) is None:
            return _safe_error(context, check_permission(selected_name, message, selected_arguments,
                                                         {tool["name"] for tool in get_available_tools()}))
        validation = validate_tool_call(selected_name, selected_arguments)
        if not validation["success"]:
            return _safe_error(context, validation)
        logger.info("llm_tool_selected=%s argument_keys=%s validation=passed",
                    safe_tool_name(selected_name), sorted(selected_arguments))
        permission = check_permission(selected_name, message, selected_arguments,
                                      {tool["name"] for tool in get_available_tools()})
        if not permission["success"]:
            return _safe_error(context, permission)
        selected_meta = _tool_info(selected_name)
        if (context["platform"] in ("google_ads", "meta_ads")
                and selected_meta["platform"] in ("google_ads", "meta_ads")
                and selected_meta["platform"] != context["platform"]):
            return _safe_error(context, make_error("Invalid Tool Call", "模型选择的工具平台与用户问题不一致"))
        if selected_name == "search_ads_knowledge" and context["platform"] in ("google_ads", "meta_ads"):
            if selected_arguments["platform"] != context["platform"]:
                return _safe_error(context, make_error("Invalid Tool Call", "检索平台与用户问题不一致"))
        if context["platform"] == "unknown":
            if selected_meta["platform"] in ("google_ads", "meta_ads"):
                context["platform"] = selected_meta["platform"]
        if context["intent"] not in ("retrieval", "memory", "progress", "steps"):
            context["intent"] = selected_meta["intent"]

    if context["platform"] == "unknown":
        return _safe_error(context, make_error("Unknown Platform", "当前 Agent 仅支持 Google Ads 和 Meta Ads"))
    if selected_name is None:
        selected_name = ROUTES.get((context["platform"], context["intent"]))
    names = _plan(context, selected_name)
    if not names or any(name is None for name in names):
        return _safe_error(context, make_error("Unsupported Learning Goal", "暂时无法识别该学习需求"))
    if len(names) > MAX_TOOL_STEPS:
        return _safe_error(context, make_error("Max Tool Steps Exceeded", "本次任务调用工具次数已达到上限",
                                               suggested_action="请将问题拆分后继续"))
    if len(names) == 2:
        context["execution_trace"].append("multi_tool_plan")
        return _run_combination(context, names)
    # 步骤主题由完整的用户原句识别，避免模型缩写 topic 后错选 Ad Set／Search。
    arguments = (_arguments_for(context, names[0]) if context["intent"] == "steps" else
                 selected_arguments if selected_name == names[0] and selected_arguments is not None else
                 _arguments_for(context, names[0]))
    return _run_single(context, names[0], arguments)
