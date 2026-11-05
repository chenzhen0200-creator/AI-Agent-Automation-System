"""集中读取环境变量；代码库不保存真实服务密钥。"""

import os


def _env_bool(name, default=False):
    """将环境变量中的 true/false 显式转换为 Python bool。"""
    value = os.getenv(name)
    return default if value is None else value.strip().casefold() in ("1", "true", "yes", "on")


def _positive_int(name, default):
    """无效的数字配置回退到安全默认值，避免服务启动失败。"""
    try:
        value = int(os.getenv(name, str(default)))
        return value if value > 0 else default
    except ValueError:
        return default


# 旧的测试任务工作流仍使用公开 API；广告学习 Agent 不调用它。
API_URL = os.getenv("API_URL", "https://jsonplaceholder.typicode.com/todos/1")
TIMEOUT_SECONDS = _positive_int("TIMEOUT_SECONDS", 10)

# 默认禁用模型；模型名称和密钥由运行环境提供，不写入代码库。
LLM_ENABLED = _env_bool("LLM_ENABLED")
MODEL_NAME = os.getenv("MODEL_NAME", "").strip()
API_KEY_ENV_NAME = os.getenv("API_KEY_ENV_NAME", "OPENAI_API_KEY")

# 外部检索使用独立密钥；未配置时不会发起搜索请求。
SEARCH_API_KEY_ENV_NAME = os.getenv("SEARCH_API_KEY_ENV_NAME", "BRAVE_SEARCH_API_KEY")

# 当前不绑定视觉服务；未来可在 Vision Client 中接入真实适配器。
VISION_ENABLED = _env_bool("VISION_ENABLED")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "")
VISION_API_KEY_ENV_NAME = os.getenv("VISION_API_KEY_ENV_NAME", "OPENAI_API_KEY")

# 浏览器跨域访问默认关闭；只接受显式列出的来源，不接受通配符。
CORS_ALLOW_ORIGINS = tuple(
    origin for origin in (item.strip() for item in os.getenv("CORS_ALLOW_ORIGINS", "").split(","))
    if origin.startswith(("https://", "http://")) and "*" not in origin
)
