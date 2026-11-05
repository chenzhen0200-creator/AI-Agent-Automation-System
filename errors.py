"""所有模块共用的结构化失败响应。"""


ERROR_GUIDANCE = {
    "Validation Error": (True, "请检查输入内容后重试"),
    "Tool Not Found": (False, "请选择已注册的学习工具"),
    "Invalid Tool Call": (False, "请重新提出明确的学习问题"),
    "LLM Not Configured": (True, "可使用规则路由继续学习"),
    "LLM Request Failed": (True, "稍后重试，或使用规则路由"),
    "Search API Not Configured": (True, "可先学习稳定概念；最新规则需核对官方文档"),
    "Search Request Failed": (True, "稍后重试外部检索"),
    "No Search Results": (True, "换用更具体的关键词查询"),
    "Official Source Not Found": (True, "调整关键词后重新查找官方资料"),
    "Content Extraction Failed": (True, "尝试其他官方页面或稍后重试"),
    "Source Rejected": (True, "请改用可信的官方来源"),
    "Vision Not Configured": (True, "请用文字描述页面，先查看通用图文步骤"),
    "Vision Request Failed": (True, "稍后重试，或使用通用图文步骤"),
    "Low Vision Confidence": (True, "请提供更清晰、完整的截图"),
    "Incomplete Screenshot": (True, "请提供包含导航栏和关键区域的完整截图"),
    "Memory Read Failed": (True, "检查本地学习记录文件后重试"),
    "Memory Write Failed": (True, "学习内容仍可查看；请稍后重试保存进度"),
    "Permission Denied": (False, "请选择允许的只读学习能力"),
    "High Risk Action Blocked": (True, "可以改为学习相关设置方法，不执行真实账户操作"),
    "Unsupported Learning Goal": (True, "请明确 Google Ads 或 Meta Ads 学习主题"),
    "Unknown Platform": (True, "请说明是 Google Ads 还是 Meta Ads"),
    "Tool Execution Error": (True, "请稍后重试或选择其他学习主题"),
    "Max Tool Steps Exceeded": (True, "请将问题拆分后继续"),
    "Screenshot Upload Not Implemented": (True, "请先用文字提问，等待截图上传接口开放"),
    "Internal Server Error": (True, "请稍后重试"),
    "Workflow Not Found": (True, "请选择已注册的自动化工作流"),
    "Workflow Disabled": (True, "等待此工作流实现并启用"),
    "Workflow Not Implemented": (True, "等待公开信息收集流程实现"),
    "Workflow Execution Failed": (True, "检查工作流日志后重试"),
    "Max Workflow Steps Exceeded": (True, "请缩小自动化任务范围"),
    "Invalid Screenshot": (True, "请提供有效的 PNG、JPEG 或 WebP 截图"),
    "Invalid Screenshot Request": (True, "请说明截图对应的学习目标"),
    "Timeout": (True, "网络超时，请稍后重试"),
    "Request Error": (True, "请检查网络连接后重试"),
    "Invalid JSON": (False, "请等待数据源恢复后重试"),
    "Missing Field": (False, "请检查数据源格式"),
}


def make_error(error_type, message=None, recoverable=None, suggested_action=None, **extra):
    """在保留原错误语义的同时补齐恢复提示。"""
    default_recoverable, default_action = ERROR_GUIDANCE.get(error_type, (False, "请稍后重试或联系维护者"))
    return {"success": False, "error_type": error_type, "message": message or error_type,
            "recoverable": default_recoverable if recoverable is None else bool(recoverable),
            "suggested_action": suggested_action or default_action, **extra}


def normalize_error(result, default_type="Tool Execution Error"):
    """兼容旧工具的错误字典，同时统一对外字段。"""
    if not isinstance(result, dict):
        return make_error(default_type, "工具未返回有效结构")
    if result.get("success") is True or result.get("ok") is True:
        return result
    return make_error(result.get("error_type", default_type), result.get("message", "操作失败"),
                      result.get("recoverable"), result.get("suggested_action"),
                      **{key: value for key, value in result.items()
                         if key not in ("success", "error_type", "message", "recoverable", "suggested_action")})
