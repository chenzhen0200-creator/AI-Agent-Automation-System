"""区分教学、诊断和真实账户操作的风险。"""

import re

from guardrails.action_policy import BLOCKED_ACTIONS, MEDIUM_RISK_ACTIONS


ACTION_WORDS = r"创建|修改|删除|复制|改成|改掉|充值|付款|支付|调整|发布|提交|授权|更改|暂停|恢复"
DIRECT_REQUEST = re.compile(rf"(?:帮我|替我|直接|现在就|自动|在我的账户).{{0,18}}(?:{ACTION_WORDS})", re.I)
SENSITIVE_OBJECT = re.compile(r"广告|campaign|ad set|账户|预算|出价|权限|付款|充值", re.I)
ENGLISH_DIRECT = re.compile(r"\b(?:create|modify|change|delete|pay|recharge|submit|publish)\b.{0,30}\b(?:campaign|ad|budget|bid|account|payment)\b", re.I)
CHINESE_MUTATION = re.compile(r"(?:创建|新建|修改|调整|更改|删除|复制|改成|改掉|暂停|发布|提交).{0,12}(?:广告|系列|预算|出价|账户|权限)|(?:充值|付款|支付).{0,8}(?:账户|广告|预算)?")
LEARNING_CUE = re.compile(r"怎么|如何|步骤|教程|解释|学习|学过|了解|在哪里|是什么|示范|指南|说明|记得|之前|上次|\bhow\b|\bexplain\b|\blearn\w*\b|\bguide\b", re.I)
DIRECT_EXECUTION = re.compile(r"帮我直接|替我|直接执行|在我的.{0,10}账户|自动帮我|给我改掉|帮我发布|直接.{0,18}(?:创建|修改|删除|发布)|帮我.{0,12}(?:创建|修改|删除|发布|调整)", re.I)
READ_ONLY_TOOLS = {"get_google_ads_steps", "get_meta_ads_steps", "get_learning_progress", "search_learning_memory", "search_ads_knowledge", "analyze_ads_screenshot", "compare_google_meta"}


def _is_read_only(tool_name):
    return tool_name in READ_ONLY_TOOLS or isinstance(tool_name, str) and tool_name.startswith(("explain_", "analyze_google_", "analyze_meta_"))


def classify_risk(tool_name=None, user_goal="", arguments=None):
    """只识别明确代为执行的高风险请求；学习提问可继续。"""
    if isinstance(tool_name, str) and tool_name in BLOCKED_ACTIONS:
        return {"risk_level": "high", "blocked_action": tool_name}
    original = user_goal if isinstance(user_goal, str) else ""
    if DIRECT_EXECUTION.search(original) and SENSITIVE_OBJECT.search(original) and not re.match(r"^\s*(?:怎么|如何|告诉我怎么|教我)", original):
        return {"risk_level": "high", "blocked_action": "real_account_change"}
    # 原句明确是教学且没有代执行语义时，模型生成的 topic 不能覆盖用户意图。
    if LEARNING_CUE.search(original) and not DIRECT_EXECUTION.search(original) and _is_read_only(tool_name):
        return {"risk_level": "medium" if tool_name in MEDIUM_RISK_ACTIONS else "low", "blocked_action": None}
    texts = [original]
    if isinstance(arguments, dict):
        texts.extend(value for key, value in arguments.items()
                     if key != "image_path" and isinstance(value, str))
    for text in texts:
        direct = DIRECT_REQUEST.search(text)
        mutation = CHINESE_MUTATION.search(text)
        english = ENGLISH_DIRECT.search(text)
        if (direct and SENSITIVE_OBJECT.search(text)
                and not LEARNING_CUE.search(text[:direct.end()])):
            return {"risk_level": "high", "blocked_action": "real_account_change"}
        if mutation and not LEARNING_CUE.search(text[:mutation.end()]):
            return {"risk_level": "high", "blocked_action": "real_account_change"}
        if english and not LEARNING_CUE.search(text[:english.end()]):
            return {"risk_level": "high", "blocked_action": "real_account_change"}
    if isinstance(tool_name, str) and tool_name in MEDIUM_RISK_ACTIONS:
        return {"risk_level": "medium", "blocked_action": None}
    return {"risk_level": "low", "blocked_action": None}
