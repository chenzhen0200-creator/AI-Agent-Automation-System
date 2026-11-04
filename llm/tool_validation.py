"""在执行前校验模型选择的工具与参数。"""

from llm.tool_schema import ALLOWED_LEARNING_TOOLS, get_tool_schema
from errors import make_error


def validate_tool_call(tool_name, arguments):
    """只允许注册表中声明的只读工具及其参数。"""
    if not isinstance(tool_name, str):
        return make_error("Invalid Tool Call", "工具名称必须是字符串")
    schema = get_tool_schema(tool_name)
    if tool_name not in ALLOWED_LEARNING_TOOLS or schema is None:
        return make_error("Invalid Tool Call", "工具未注册或不允许执行")
    if not isinstance(arguments, dict):
        return make_error("Invalid Tool Call", "工具参数必须是对象")
    parameters = schema["parameters"]
    properties = parameters["properties"]
    for name in parameters["required"]:
        if name not in arguments:
            return make_error("Invalid Tool Call", f"缺少必需参数：{name}")
    for name, value in arguments.items():
        if name not in properties:
            return make_error("Invalid Tool Call", f"不允许的参数：{name}")
        rule = properties[name]
        allowed_types = rule["type"] if isinstance(rule["type"], list) else [rule["type"]]
        if value is None and "null" in allowed_types:
            continue
        if "boolean" in allowed_types and isinstance(value, bool):
            continue
        if "string" not in allowed_types or not isinstance(value, str) or not value.strip() or len(value) > 1000:
            return make_error("Invalid Tool Call", f"参数 {name} 类型不正确或为空")
        if "enum" in rule and value not in rule["enum"]:
            return make_error("Invalid Tool Call", f"参数 {name} 不在允许范围内")
    return {"success": True, "tool_name": tool_name, "arguments": arguments}
