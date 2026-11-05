"""可选的 OpenAI Responses API 客户端；默认不发起模型请求。"""

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import API_KEY_ENV_NAME, LLM_ENABLED, MODEL_NAME
from errors import make_error
from prompts.system_prompt import SYSTEM_PROMPT
from recovery.retry_policy import run_with_retry
from tools.log_tool import logger, safe_tool_name


RESPONSES_URL = "https://api.openai.com/v1/responses"
SAFE_CODE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]{0,79}$")


def _safe_code(value, fallback):
    """只允许短的错误代码进入日志，绝不记录服务端原始报错或密钥。"""
    if (isinstance(value, str) and SAFE_CODE.fullmatch(value)
            and not value.lower().startswith(("sk-", "ghp_", "github_pat_"))):
        return value
    return fallback


def _http_error_kind(error):
    defaults = {400: "bad_request", 401: "authentication_error", 403: "permission_denied",
                404: "model_not_found", 429: "rate_limit_exceeded"}
    fallback = defaults.get(error.code, "server_error" if error.code >= 500 else "http_error")
    try:
        payload = json.loads(error.read(4096).decode("utf-8"))
        details = payload.get("error", {}) if isinstance(payload, dict) else {}
        if not isinstance(details, dict):
            return fallback
        return _safe_code(details.get("code") or details.get("type"), fallback)
    except (OSError, UnicodeDecodeError, ValueError, TypeError):
        return fallback


def _failure(error_type, summary, status_code=None, provider_error_type=None, retryable=False):
    """失败日志仅写安全分类，不写用户问题、响应正文或 API Key。"""
    kind = provider_error_type or error_type
    logger.warning("LLM request failed error_type=%s status_code=%s message=%s",
                   kind, status_code if status_code is not None else "none", summary)
    extra = {"retryable": retryable}
    if status_code is not None:
        extra["status_code"] = status_code
    if provider_error_type is not None:
        extra["provider_error_type"] = provider_error_type
    return make_error(error_type, summary, **extra)


def choose_action(user_message, available_tools):
    """请求模型选择一个工具或直接回答；不执行任何工具。"""
    api_key = os.getenv(API_KEY_ENV_NAME, "")
    model_label = _safe_code(MODEL_NAME, "unset_or_invalid")
    logger.info("LLM request started model=%s llm_enabled=%s api_key_configured=%s",
                model_label, str(LLM_ENABLED).lower(), str(bool(api_key)).lower())
    if not LLM_ENABLED or not MODEL_NAME or not api_key:
        reason = "llm_disabled" if not LLM_ENABLED else "model_name_missing" if not MODEL_NAME else "api_key_missing"
        return _failure("LLM Not Configured", reason)

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
            kind = _http_error_kind(error)
            retryable = (error.code == 429 and kind != "insufficient_quota") or 500 <= error.code < 600
            return _failure("LLM Request Failed", kind, error.code, kind, retryable)
        except (URLError, TimeoutError) as error:
            kind = "timeout" if isinstance(error, TimeoutError) or isinstance(getattr(error, "reason", None), TimeoutError) else "network_error"
            return _failure("LLM Request Failed", kind, provider_error_type=kind, retryable=True)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _failure("LLM Request Failed", "invalid_json", provider_error_type="invalid_json")

    response, retry_count = run_with_retry(request_once, "llm_model")
    if not response["success"]:
        response["retry_count"] = retry_count
        return response
    payload = response["payload"]

    if not isinstance(payload, dict):
        return _failure("LLM Request Failed", "invalid_response", provider_error_type="invalid_response")
    output = payload.get("output", [])
    if not isinstance(output, list):
        return _failure("LLM Request Failed", "invalid_response", provider_error_type="invalid_response")
    calls = [item for item in output if isinstance(item, dict) and item.get("type") == "function_call"]
    if len(calls) > 1:
        return _failure("Invalid Tool Call", "multiple_tool_calls")
    if calls:
        call = calls[0]
        try:
            arguments = json.loads(call["arguments"])
            name = call["name"]
        except (KeyError, TypeError, json.JSONDecodeError):
            return _failure("Invalid Tool Call", "invalid_tool_call")
        logger.info("LLM request succeeded tool_name=%s", safe_tool_name(name))
        return {"success": True, "type": "tool_call", "tool_name": name, "arguments": arguments, "retry_count": retry_count}

    texts = [part.get("text", "") for item in output if isinstance(item, dict) and item.get("type") == "message"
             for part in (item.get("content") if isinstance(item.get("content"), list) else [])
             if isinstance(part, dict) and part.get("type") == "output_text"]
    content = "\n".join(text for text in texts if text).strip()
    if content:
        logger.info("LLM request succeeded")
        return {"success": True, "type": "direct_answer", "content": content, "retry_count": retry_count}
    return _failure("LLM Request Failed", "empty_response", provider_error_type="empty_response")
