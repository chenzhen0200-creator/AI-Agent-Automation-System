"""集中登记 Agent 可以选择并执行的能力。"""

from tools.google_ads_concept_tool import explain_google_ads_concept
from tools.google_ads_steps_tool import get_google_ads_steps
from tools.google_ads_analysis_tool import analyze_google_ads_case
from tools.meta_ads_concept_tool import explain_meta_ads_concept
from tools.meta_ads_steps_tool import get_meta_ads_steps
from tools.meta_ads_analysis_tool import analyze_meta_ads_case
from tools.compare_platforms_tool import compare_google_meta
from tools.learning_progress_tool import get_learning_progress
from tools.memory_search_tool import search_learning_memory
from tools.ads_knowledge_search_tool import search_ads_knowledge
from tools.screenshot_analysis_tool import analyze_ads_screenshot
from errors import make_error, normalize_error
from guardrails.permission_guard import check_permission
from tools.log_tool import logger, safe_tool_name


TOOLS = [
    {"name": "explain_google_ads_concept", "platform": "google_ads", "intent": "concept", "description": "解释 Google Ads 指标、追踪、广告类型和出价概念", "handler": explain_google_ads_concept},
    {"name": "get_google_ads_steps", "platform": "google_ads", "intent": "steps", "description": "讲解 Google Ads 界面位置和分步骤操作学习路径", "handler": get_google_ads_steps},
    {"name": "analyze_google_ads_case", "platform": "google_ads", "intent": "analysis", "description": "分析 Google Ads 指标异常和投放案例", "handler": analyze_google_ads_case},
    {"name": "explain_meta_ads_concept", "platform": "meta_ads", "intent": "concept", "description": "解释 Meta Ads 结构、追踪、受众和指标概念", "handler": explain_meta_ads_concept},
    {"name": "get_meta_ads_steps", "platform": "meta_ads", "intent": "steps", "description": "讲解 Meta Ads 界面位置和分步骤操作学习路径", "handler": get_meta_ads_steps},
    {"name": "analyze_meta_ads_case", "platform": "meta_ads", "intent": "analysis", "description": "分析 Meta Ads 指标异常、受众和素材案例", "handler": analyze_meta_ads_case},
    {"name": "compare_google_meta", "platform": "cross_platform", "intent": "comparison", "description": "比较 Google Ads 与 Meta Ads 的广告、追踪、受众、出价、归因和结构", "handler": compare_google_meta},
    {"name": "get_learning_progress", "platform": "cross_platform", "intent": "progress", "description": "读取两平台已学主题、阶段和下一步建议", "handler": get_learning_progress},
    {"name": "search_learning_memory", "platform": "cross_platform", "intent": "memory", "description": "只读搜索用户是否学过某主题，或读取最近学习记录；可按平台筛选", "handler": search_learning_memory},
    {"name": "search_ads_knowledge", "platform": "cross_platform", "intent": "retrieval", "description": "只读检索 Google Ads 或 Meta Ads 的最新规则、界面和官方文档，返回来源与相关正文", "handler": search_ads_knowledge},
    {"name": "analyze_ads_screenshot", "platform": "cross_platform", "intent": "screenshot", "description": "只读分析用户上传的 Google Ads 或 Meta Ads 后台截图；识别页面控件，并结合标准步骤提供学习指导；仅收到真实图片时使用", "handler": analyze_ads_screenshot},
]


def get_available_tools():
    """返回可供 Agent 查看或展示的工具信息，不暴露函数对象。"""
    return [{key: tool[key] for key in ("name", "platform", "intent", "description")} for tool in TOOLS]


def execute_tool(tool_name, *args, policy_context=None, **kwargs):
    """所有路径统一经过权限检查，失败时只记录安全元数据。"""
    context = policy_context if isinstance(policy_context, dict) else {}
    fallback_label = context.get("fallback_used") if context.get("fallback_used") in ("none", "rule_router", "stable_tool", "steps_tool") else "none"
    goal = context.get("user_goal") or kwargs.get("user_goal") or kwargs.get("query")
    if not isinstance(goal, str):
        goal = args[0] if args and isinstance(args[0], str) else ""
    arguments = context.get("arguments") or kwargs
    permission = check_permission(tool_name, goal, arguments, {item["name"] for item in TOOLS})
    if not permission["success"]:
        logger.warning("tool=%s error_type=%s recoverable=%s retry_count=0 fallback_used=%s risk_level=%s blocked_action=%s",
                       safe_tool_name(tool_name), permission["error_type"], permission["recoverable"], fallback_label,
                       permission["risk_level"], permission.get("blocked_action"))
        return permission
    tool = next((item for item in TOOLS if item["name"] == tool_name), None)
    if tool is None:
        return make_error("Tool Not Found", "未找到可用工具")
    try:
        result = tool["handler"](*args, **kwargs)
    except Exception as error:
        logger.error("tool=%s error_type=Tool Execution Error exception_type=%s", safe_tool_name(tool_name), type(error).__name__)
        result = make_error("Tool Execution Error", "教学工具执行失败")
    if not isinstance(result, dict) or result.get("success") is not True:
        result = normalize_error(result)
    logger.info("tool=%s error_type=%s recoverable=%s retry_count=%s fallback_used=%s risk_level=%s blocked_action=%s",
                safe_tool_name(tool_name), result.get("error_type", "none"), result.get("recoverable", False),
                result.get("retry_count", 0), fallback_label, permission["risk_level"],
                permission.get("blocked_action"))
    return result
