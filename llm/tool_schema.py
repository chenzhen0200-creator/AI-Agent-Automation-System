"""把只读工具注册信息转换为 Function Calling Schema。"""

from tools.tool_registry import get_available_tools


# 明确允许暴露给模型的十一个只读学习工具；新增工具需显式审核。
ALLOWED_LEARNING_TOOLS = frozenset({
    "explain_google_ads_concept", "explain_meta_ads_concept",
    "get_google_ads_steps", "get_meta_ads_steps",
    "analyze_google_ads_case", "analyze_meta_ads_case",
    "compare_google_meta", "get_learning_progress",
    "search_learning_memory",
    "search_ads_knowledge",
    "analyze_ads_screenshot",
})

ARGUMENTS = {
    "concept": ("topic", "要解释的广告概念或用户原问题"),
    "steps": ("topic", "要学习的界面主题或用户原问题"),
    "analysis": ("issue", "用户遇到的广告问题或案例"),
    "comparison": ("topic", "要比较的 Google Ads 与 Meta Ads 主题"),
}


def get_tool_schemas():
    """根据注册表生成十一个严格的只读函数定义。"""
    schemas = []
    for tool in get_available_tools():
        if tool["name"] not in ALLOWED_LEARNING_TOOLS:
            continue
        argument = ARGUMENTS.get(tool["intent"])
        if tool["intent"] == "memory":
            # 严格模式要求所有字段在 required 中；null 表示不限定平台或主题。
            properties = {
                "platform": {"type": ["string", "null"], "enum": ["google_ads", "meta_ads", "cross_platform", None],
                             "description": "要查询的平台；不限定时用 null"},
                "topic": {"type": ["string", "null"], "description": "要搜索的主题；查询最近学习时用 null"},
            }
        elif tool["intent"] == "retrieval":
            properties = {
                "platform": {"type": "string", "enum": ["google_ads", "meta_ads", "cross_platform"], "description": "要检索的广告平台"},
                "query": {"type": "string", "description": "用户需要核实的最新平台规则或官方说明"},
                "official_only": {"type": "boolean", "description": "只使用官方来源；默认应为 true"},
                "freshness_required": {"type": "boolean", "description": "是否优先检索近期资料"},
            }
        elif tool["intent"] == "screenshot":
            properties = {
                "image_path": {"type": "string", "description": "用户本次上传的本地截图路径；禁止编造路径"},
                "user_goal": {"type": "string", "description": "用户希望针对截图学习的问题"},
                "platform_hint": {"type": "string", "enum": ["google_ads", "meta_ads", "unknown"],
                                  "description": "根据用户文字给出的平台提示；不确定时用 unknown"},
            }
        else:
            properties = {} if argument is None else {argument[0]: {"type": "string", "description": argument[1]}}
        schemas.append({
            "type": "function",
            "name": tool["name"],
            "description": f"[{tool['platform']}] {tool['description']}；只读学习能力，不操作广告账户。",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            },
            "strict": True,
        })
    return schemas


def get_tool_schema(tool_name):
    """按名称取得 Schema，供执行前校验。"""
    return next((schema for schema in get_tool_schemas() if schema["name"] == tool_name), None)
