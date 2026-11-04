"""区分教学、诊断和真实账户操作的风险。"""

import re

from guardrails.action_policy import BLOCKED_ACTIONS, MEDIUM_RISK_ACTIONS


ACTION_WORDS = r"创建|修改|删除|充值|付款|支付|调整|发布|提交|授权|更改|暂停|恢复"
DIRECT_REQUEST = re.compile(rf"(?:帮我|替我|直接|现在就|自动|在我的账户).{{0,18}}(?:{ACTION_WORDS})", re.I)
SENSITIVE_OBJECT = re.compile(r"广告|campaign|ad set|账户|预算|出价|权限|付款|充值", re.I)
ENGLISH_DIRECT = re.compile(r"\b(?:create|modify|change|delete|pay|recharge|submit|publish)\b.{0,30}\b(?:campaign|ad|budget|bid|account|payment)\b", re.I)
CHINESE_MUTATION = re.compile(r"(?:创建|新建|修改|调整|更改|删除|暂停|发布|提交).{0,12}(?:广告|系列|预算|出价|账户|权限)|(?:充值|付款|支付).{0,8}(?:账户|广告|预算)?")
LEARNING_CUE = re.compile(r"怎么|如何|步骤|教程|解释|学习|学过|了解|在哪里|是什么|示范|指南|说明|记得|之前|上次|\bhow\b|\bexplain\b|\blearn\w*\b|\bguide\b", re.I)


def classify_risk(tool_name=None, user_goal="", arguments=None):
    """只识别明确代为执行的高风险请求；学习提问可继续。"""
    if isinstance(tool_name, str) and tool_name in BLOCKED_ACTIONS:
        return {"risk_level": "high", "blocked_action": tool_name}
    texts = [user_goal] if isinstance(user_goal, str) else []
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
