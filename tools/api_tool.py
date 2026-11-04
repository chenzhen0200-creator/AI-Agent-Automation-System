"""请求公开测试 API，并把响应整理为统一结果。"""

import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from config import API_URL, TIMEOUT_SECONDS
from errors import make_error


def fetch_task():
    """成功时返回数据，失败时返回错误类型和信息。"""
    try:
        # 超时时间从配置文件读取，避免请求一直等待。
        with urlopen(API_URL, timeout=TIMEOUT_SECONDS) as response:
            # 先读取响应内容，再将 JSON 转换为 Python 数据。
            data = json.loads(response.read().decode("utf-8"))
        return {"ok": True, "data": data}

    except TimeoutError:
        return {"ok": False, **make_error("Timeout", "请求超时，请稍后重试。")}
    except (HTTPError, URLError) as error:
        # 某些网络环境会把超时包装在 URLError 中。
        if isinstance(getattr(error, "reason", None), TimeoutError):
            return {"ok": False, **make_error("Timeout", "请求超时，请稍后重试。")}
        return {"ok": False, **make_error("Request Error", "请求失败，请检查网络连接。")}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {"ok": False, **make_error("Invalid JSON", "API 返回的内容不是有效的 JSON。")}
