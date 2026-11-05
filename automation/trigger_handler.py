"""将手动、定时与 Webhook 事件转成同一工作流调用。"""

import hmac
import os

from automation.workflow_runner import run_workflow
from errors import make_error


TRIGGER_TYPES = frozenset({"manual", "schedule", "webhook"})


def handle_trigger(workflow_name, trigger_type, inputs=None, token=None):
    if trigger_type not in TRIGGER_TYPES:
        return make_error("Validation Error", "不支持的触发类型")
    if not isinstance(workflow_name, str) or not workflow_name or len(workflow_name) > 80:
        return make_error("Validation Error", "无效的工作流名称")
    if inputs is None:
        inputs = {}
    if not isinstance(inputs, dict):
        return make_error("Validation Error", "inputs 必须是对象")
    if trigger_type != "manual":
        expected = os.getenv("AUTOMATION_WEBHOOK_TOKEN", "")
        if not expected or not isinstance(token, str) or not hmac.compare_digest(token, expected):
            return make_error("Permission Denied", "Webhook 或定时触发尚未授权")
    return run_workflow(workflow_name, trigger_type, inputs)
