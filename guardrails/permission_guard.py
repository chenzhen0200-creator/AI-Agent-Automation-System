"""在任何工具 handler 执行前做权限和风险检查。"""

from errors import make_error
from guardrails.action_policy import ALLOWED_ACTIONS
from guardrails.risk_classifier import classify_risk


def check_permission(tool_name, user_goal="", arguments=None, registered_names=None):
    """高风险先拦截；未知或未授权工具永不进入 handler。"""
    if not isinstance(tool_name, str):
        return make_error("Invalid Tool Call", "工具名称必须是字符串", risk_level="low", blocked_action=None)
    risk = classify_risk(tool_name, user_goal, arguments)
    if risk["risk_level"] == "high":
        message = ("当前学习 Agent 不允许修改真实广告预算" if risk["blocked_action"] in ("update_campaign_budget", "modify_budget")
                   else "当前学习 Agent 不允许执行真实广告账户操作")
        return make_error("High Risk Action Blocked", message,
                          suggested_action="可以改为学习相关设置方法", **risk)
    if registered_names is not None and tool_name not in registered_names:
        return make_error("Tool Not Found", "未找到可用工具", **risk)
    if tool_name not in ALLOWED_ACTIONS:
        return make_error("Permission Denied", "此工具不在只读学习白名单中", **risk)
    return {"success": True, **risk}
