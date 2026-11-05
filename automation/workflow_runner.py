"""受限的自动化执行链；只运行已登记的只读工作流。"""

from datetime import datetime, timezone

from automation.workflow_context import new_context
from automation.workflow_registry import get_workflow
from errors import make_error, normalize_error
from guardrails.permission_guard import check_permission
from guardrails.risk_classifier import classify_risk
from llm.tool_validation import validate_tool_call
from recovery.retry_policy import run_with_retry
from tools.log_tool import logger, safe_tool_name
from tools.tool_registry import execute_tool, get_available_tools


MAX_WORKFLOW_STEPS = 10


def run_workflow(workflow_name, trigger_type="manual", inputs=None):
    """校验工作流并执行；每次工具尝试都受步骤上限和权限约束。"""
    if not isinstance(inputs, dict):
        inputs = {}
    context = new_context(workflow_name, trigger_type, inputs)
    workflow = get_workflow(workflow_name)
    error = None
    output = None
    if workflow is None:
        error = make_error("Workflow Not Found", "未找到自动化工作流")
    elif not workflow["enabled"]:
        error = make_error("Workflow Disabled", "此自动化工作流尚未启用")
    elif trigger_type not in workflow["trigger_type"]:
        error = make_error("Validation Error", "此工作流不支持该触发类型")
    elif workflow["risk_level"] == "high":
        error = make_error("High Risk Action Blocked", "自动化工作流不得执行真实广告账户操作")
    else:
        context["execution_trace"].extend(("workflow_registered", "workflow_guardrail_passed"))

        def run_tool(name, arguments):
            context["execution_trace"].append("tool_validation")
            validation = validate_tool_call(name, arguments)
            if not validation["success"]:
                return validation
            risk = classify_risk(name, arguments.get("query", ""), arguments)
            context["execution_trace"].append("risk_classification:" + risk["risk_level"])
            permission = check_permission(name, arguments.get("query", ""), arguments,
                                          {item["name"] for item in get_available_tools()})
            if not permission["success"]:
                return permission

            def attempt():
                if context["step_count"] >= MAX_WORKFLOW_STEPS:
                    return make_error("Max Workflow Steps Exceeded", "自动化工具调用次数已达到上限")
                context["step_count"] += 1
                context["execution_trace"].append("tool_execution:" + name)
                return execute_tool(name, policy_context={"user_goal": arguments.get("query", ""),
                                                      "arguments": arguments}, **arguments)

            result, retries = run_with_retry(attempt, name)
            context["retry_count"] += retries + result.get("retry_count", 0)
            context["tool_results"].append({"tool_name": name, "result": result})
            return result

        try:
            output = workflow["handler"](context, run_tool)
            if not isinstance(output, dict):
                error = make_error("Workflow Execution Failed", "工作流未返回结构化结果")
            elif not output.get("success"):
                error = normalize_error(output)
        except Exception as exc:
            logger.error("workflow_exception workflow_name=%s exception_type=%s",
                         safe_tool_name(workflow_name), type(exc).__name__)
            error = make_error("Workflow Execution Failed", "自动化工作流执行失败")

    context["status"] = "failed" if error else "completed"
    context["execution_trace"].append("workflow_" + context["status"])
    finished_at = datetime.now(timezone.utc).isoformat()
    logger.info("workflow_name=%s trigger_type=%s started_at=%s finished_at=%s steps_executed=%s retry_count=%s fallback_used=%s final_status=%s",
                safe_tool_name(workflow_name), trigger_type, context["started_at"], finished_at,
                context["step_count"], context["retry_count"], context["fallback_used"], context["status"])
    result = {
        "success": error is None, "workflow_name": workflow_name, "trigger_type": trigger_type,
        "status": context["status"], "started_at": context["started_at"], "finished_at": finished_at,
        "steps_executed": context["step_count"], "retry_count": context["retry_count"],
        "results": context["tool_results"], "warnings": context["warnings"],
        "execution_trace": context["execution_trace"],
    }
    if error:
        result.update({key: error[key] for key in ("error_type", "message", "recoverable", "suggested_action")})
    else:
        result["output"] = {key: value for key, value in output.items() if key != "success"}
    return result
