"""可选的 OpenAI Responses API 客户端；默认不发起模型请求。"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import API_KEY_ENV_NAME, LLM_ENABLED, MODEL_NAME
from errors import make_error
from prompts.system_prompt import SYSTEM_PROMPT
from recovery.retry_policy import run_with_retry


RESPONSES_URL = "https://api.openai.com/v1/responses"


def choose_action(user_message, available_tools):
    """请求模型选择一个工具或直接回答；不执行任何工具。"""
    api_key = os.getenv(API_KEY_ENV_NAME, "")
    if not LLM_ENABLED or not MODEL_NAME or not api_key:
        return make_error("LLM Not Configured", "当前未配置真实 LLM，无法执行 Tool Calling")

    body = {
        "model": MODEL_NAME,
        "instructions": SYSTEM_PROMPT,
        "input": user_message,
        "tools": available_tools,
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "store": False,
    }
    request = Request(
        RESPONSES_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    def request_once():
        try:
            with urlopen(request, timeout=20) as response:
                return {"success": True, "payload": json.loads(response.read().decode("utf-8"))}
        except HTTPError as error:
            # 不读取响应体；只重试 429 与临时服务端错误。
            return make_error("LLM Request Failed", f"模型请求失败（HTTP {error.code}）",
                              retryable=error.code == 429 or 500 <= error.code < 600)
        except (URLError, TimeoutError):
            return make_error("LLM Request Failed", "模型网络请求失败", retryable=True)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return make_error("LLM Request Failed", "模型响应解析失败")

    response, retry_count = run_with_retry(request_once, "llm_model")
    if not response["success"]:
        response["retry_count"] = retry_count
        return response
    payload = response["payload"]

    if not isinstance(payload, dict):
        return make_error("LLM Request Failed", "模型响应格式不正确", retry_count=retry_count)
    output = payload.get("output", [])
    if not isinstance(output, list):
        return make_error("LLM Request Failed", "模型响应格式不正确", retry_count=retry_count)
    calls = [item for item in output if isinstance(item, dict) and item.get("type") == "function_call"]
    if len(calls) > 1:
        return make_error("Invalid Tool Call", "当前一次只允许调用一个工具", retry_count=retry_count)
    if calls:
        call = calls[0]
        try:
            arguments = json.loads(call["arguments"])
            name = call["name"]
        except (KeyError, TypeError, json.JSONDecodeError):
            return make_error("Invalid Tool Call", "模型返回的工具调用格式不正确", retry_count=retry_count)
        return {"success": True, "type": "tool_call", "tool_name": name, "arguments": arguments, "retry_count": retry_count}

    texts = [part.get("text", "") for item in output if isinstance(item, dict) and item.get("type") == "message"
             for part in (item.get("content") if isinstance(item.get("content"), list) else [])
             if isinstance(part, dict) and part.get("type") == "output_text"]
    content = "\n".join(text for text in texts if text).strip()
    if content:
        return {"success": True, "type": "direct_answer", "content": content, "retry_count": retry_count}
    return make_error("LLM Request Failed", "模型没有返回可用内容", retry_count=retry_count)
