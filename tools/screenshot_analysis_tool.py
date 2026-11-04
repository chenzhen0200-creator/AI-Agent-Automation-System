"""组合真实截图观察与现有图文步骤；只给学习建议。"""

import re

from config import VISION_ENABLED, VISION_MODEL_NAME
from tools.google_ads_steps_tool import ALIASES as GOOGLE_ALIASES
from tools.meta_ads_steps_tool import ALIASES as META_ALIASES
from tools.log_tool import logger
from vision.screenshot_analyzer import analyze_screenshot
from errors import make_error, normalize_error


STEP_WORDS = ("在哪里", "点哪个", "下一步", "怎么添加", "怎么修改", "怎么删除", "之前的设置在哪里看", "怎么设置", "怎么创建")


def _match_label(step, analysis):
    """只接受截图中明确可见且未禁用的控件。"""
    labels = re.findall(r"“([^”]+)”", step.get("action", ""))
    if not labels:
        return None
    options = [part.strip().casefold() for part in re.split(r"[／/]", labels[0]) if part.strip()]
    current = analysis["current_page"].casefold()
    if any(option == current or option + "s" == current for option in options):
        return None  # 当前已在该页面，不重复推荐导航动作。
    for element in analysis["visible_elements"]:
        if (element["element_type"] not in ("button", "tab", "menu") or element["state"] == "disabled"
                or element["confidence"] < 0.7):
            continue
        label = element["text"].casefold()
        if any(option == label or option in label for option in options):
            return element
    if analysis["confidence"] >= 0.85:
        for label in analysis["visible_navigation"]:
            if any(option == label.casefold() or option in label.casefold() for option in options):
                return {"text": label, "location": "截图中可见的导航区域"}
    return None


def analyze_ads_screenshot(image_path, user_goal, platform_hint="unknown", adapter=None, defer_steps=False):
    """视觉分析成功后，才请求对应 Steps Tool 并寻找可信下一步。"""
    logger.info("截图分析：received=%s", bool(image_path))
    if not isinstance(user_goal, str) or not user_goal.strip() or platform_hint not in ("google_ads", "meta_ads", "unknown"):
        return make_error("Invalid Screenshot Request", "截图学习目标或平台提示无效")
    if re.search(r"(帮我|替我|直接|现在就|在我的账户).{0,16}(创建|修改|删除|充值|付款|支付|调整|发布)", user_goal):
        return make_error("High Risk Action Blocked", "截图工具只提供学习指导，不操作真实广告账户")
    analysis = analyze_screenshot(image_path, user_goal, platform_hint, adapter=adapter)
    logger.info("Vision 已配置=%s analysis_success=%s platform=%s page=%s elements=%s confidence=%s steps_called=%s",
                bool(VISION_ENABLED and VISION_MODEL_NAME and adapter is not None), analysis.get("success", False),
                analysis.get("platform", "unknown"),
                analysis.get("current_page", "unknown"), len(analysis.get("visible_elements", [])),
                analysis.get("confidence", "unknown"), False)
    if not analysis["success"]:
        return analysis
    result = {key: value for key, value in analysis.items() if key != "success"}
    result.update({"user_goal": user_goal, "recommended_step": None, "standard_steps": [],
                   "steps_called": False, "screenshot_guidance": "已识别当前页面；请说明希望学习的具体控件或操作。",
                   "retrieval_suggestion": None})
    # 截图中如提示界面变更，只预留外部检索建议，不自动串联网络请求。
    if any(word in user_goal for word in ("最新", "现在", "新版", "最近更新")):
        result["retrieval_suggestion"] = "如界面已更新，可另用 search_ads_knowledge 核对官方说明"
    if not any(word in user_goal for word in STEP_WORDS):
        if "审核状态" in user_goal or "review status" in user_goal.casefold():
            status = analysis.get("review_status")
            result["screenshot_guidance"] = (f"截图可见的审核状态为“{status}”；具体含义请结合官方说明核对。"
                                             if status else "截图中未可靠识别审核状态，请提供包含状态栏的完整截图。")
        elif any(word in user_goal for word in ("为什么这里", "为什么显示", "这个提示")):
            warnings = analysis.get("warning_messages", [])
            result["screenshot_guidance"] = (f"截图可见提示：“{warnings[0]}”。可先核对对应设置；截图无法单独证明原因。"
                                             if warnings else "截图中未可靠识别提示文字，请提供包含提示区域的完整截图。")
        elif "这个是什么" in user_goal:
            selected = analysis.get("selected_items", [])
            result["screenshot_guidance"] = (f"截图中选中的项目为“{selected[0]}”；如需解释其他控件，请指出名称或位置。"
                                             if len(selected) == 1 else "请指出要解释的控件名称或在截图中的位置。")
        return {"success": True, **result}
    aliases = GOOGLE_ALIASES if analysis["platform"] == "google_ads" else META_ALIASES
    has_topic = any(alias in user_goal.casefold() for words in aliases.values() for alias in words)
    if not has_topic and "下一步" not in user_goal:
        result["screenshot_guidance"] = "已识别当前页面，但目标控件不明确；请说明要找的设置或按钮。"
        return {"success": True, **result}
    # Agent 可要求先返回视觉结果，由主流程再受控调用 Steps Tool。
    steps_name = "get_google_ads_steps" if analysis["platform"] == "google_ads" else "get_meta_ads_steps"
    topic_query = user_goal if has_topic else analysis["current_page"]
    if defer_steps:
        result["steps_requested"] = True
        result["steps_topic_query"] = topic_query
        return {"success": True, **result}
    from tools.tool_registry import execute_tool
    steps_result = execute_tool(steps_name, topic_query)
    return combine_screenshot_with_steps({"success": True, **result}, steps_result)


def combine_screenshot_with_steps(screenshot_result, steps_result):
    """由 Agent 在两次受控 Tool 调用后合并图文指导。"""
    result = {key: value for key, value in screenshot_result.items()
              if key not in ("success", "steps_requested", "steps_topic_query")}
    result["steps_called"] = True
    logger.info("Vision 步骤联动：platform=%s page=%s elements=%s confidence=%.2f steps_called=%s",
                result["platform"], result["current_page"], len(result["visible_elements"]),
                result["confidence"], True)
    if not steps_result.get("success"):
        result["screenshot_guidance"] = "已识别截图，但暂时无法取得对应的标准步骤。"
        result["warnings"] = [normalize_error(steps_result)]
        return {"success": True, **result}
    result["steps_topic"] = steps_result["topic"]
    result["standard_steps"] = steps_result["steps"]
    for step in steps_result["steps"]:
        element = _match_label(step, result)
        if element is None:
            continue
        result["recommended_step"] = {
            "title": step["title"], "ui_location": element.get("location") or step["ui_location"],
            "action": step["action"], "expected_result": step["next_page"],
            "image_hint": step["image_hint"],
        }
        result["screenshot_guidance"] = (
            f"当前位于 {result['current_page']}。截图中可见“{element['text']}”，"
            f"可按学习步骤了解：{step['action']}，预计进入 {step['next_page']}。请先核对当前界面。"
        )
        break
    if result["recommended_step"] is None:
        result["screenshot_guidance"] = "已找到标准步骤，但截图中未可靠识别对应控件；请提供包含该区域的完整截图。"
    return {"success": True, **result}
