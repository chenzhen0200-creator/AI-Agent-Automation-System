"""云端 FastAPI 入口；CLI 仍由 main.py 提供。"""

import traceback
import os
from uuid import UUID
from pathlib import Path

from fastapi import FastAPI, Header, Request, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from agents.ads_learning_agent import run_ads_learning_agent
from api.schemas import AgentResponse, AutomationRequest, AutomationResponse, ChatRequest, ConversationRequest, WebhookRequest
from database.connection import configured as database_configured, connected as database_connected
from database.conversation_repository import create_conversation, delete_conversation, get_conversation, list_conversations
from database.message_repository import list_messages, save_message
from automation.trigger_handler import handle_trigger
from config import API_KEY_ENV_NAME, CORS_ALLOW_ORIGINS, LLM_ENABLED, MODEL_NAME, SEARCH_API_KEY_ENV_NAME, VISION_ENABLED
from errors import make_error
from tools.log_tool import logger
from tools.tool_registry import execute_tool


app = FastAPI(title="AdLearn", description="AdLearn 是用于 Google Ads 和 Meta Ads 学习与自动化的 AI Agent。", debug=False)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# 默认不允许跨站浏览器请求；未来前端域名通过环境变量逐一配置。
if CORS_ALLOW_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(CORS_ALLOW_ORIGINS),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )


@app.exception_handler(RequestValidationError)
def handle_validation_error(_request: Request, _error: RequestValidationError):
    """不回显用户提交的字段值或内部校验细节。"""
    return JSONResponse(status_code=422, content=make_error("Validation Error", "请求格式无效"))


@app.exception_handler(Exception)
def handle_internal_error(_request: Request, error: Exception):
    """仅在服务器日志记录异常类型与调用栈，对外返回安全错误。"""
    logger.error("api_internal_error exception_type=%s stack=%s",
                 type(error).__name__, traceback.format_tb(error.__traceback__))
    return JSONResponse(status_code=500,
                        content=make_error("Internal Server Error", "服务处理请求时发生错误"))


@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/api/status")
def api_status():
    """只暴露布尔状态，绝不返回密钥、模型提示词或环境变量值。"""
    return {"service": "online", "service_name": "AdLearn", "llm_enabled": bool(LLM_ENABLED and MODEL_NAME and os.getenv(API_KEY_ENV_NAME)),
            "vision_enabled": VISION_ENABLED, "search_configured": bool(os.getenv(SEARCH_API_KEY_ENV_NAME)),
            "database_configured": database_configured(), "database_connected": database_connected()}


def _client_id(value):
    try:
        return str(UUID(value))
    except (TypeError, ValueError, AttributeError):
        raise HTTPException(status_code=422, detail="无效的 client_id")


def _conversation_id(value):
    try:
        return str(UUID(value))
    except (TypeError, ValueError, AttributeError):
        raise HTTPException(status_code=422, detail="无效的 conversation_id")


def _history_available():
    if not database_configured():
        raise HTTPException(status_code=503, detail="Database Not Configured")


@app.get("/conversations")
def conversations(client_id: str = Query(min_length=36, max_length=36)):
    _history_available()
    return {"success": True, "conversations": list_conversations(_client_id(client_id))}


@app.post("/conversations")
def new_conversation(request: ConversationRequest):
    _history_available()
    return {"success": True, "conversation": create_conversation(_client_id(request.client_id), request.title.strip() or "新对话")}


@app.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: str, client_id: str = Query(min_length=36, max_length=36)):
    _history_available()
    owner = _client_id(client_id)
    target = _conversation_id(conversation_id)
    if not get_conversation(target, owner):
        raise HTTPException(status_code=404, detail="未找到对话")
    return {"success": True, "messages": list_messages(target, owner)}


@app.delete("/conversations/{conversation_id}")
def remove_conversation(conversation_id: str, client_id: str = Query(min_length=36, max_length=36)):
    _history_available()
    if not delete_conversation(_conversation_id(conversation_id), _client_id(client_id)):
        raise HTTPException(status_code=404, detail="未找到对话")
    return {"success": True}


@app.get("/health")
def health():
    # 只确认 Web 进程能响应；不调用模型、搜索、视觉或广告账户。
    return {"status": "ok"}


@app.get("/learning-progress")
def learning_progress():
    """通过原有只读 Tool Registry 获取学习进度。"""
    return execute_tool("get_learning_progress", policy_context={"user_goal": "读取学习进度"})


@app.post("/chat", response_model=AgentResponse, response_model_exclude_unset=True)
def chat(request: ChatRequest):
    """执行文字学习问题；服务器不能访问客户端电脑的本地路径。"""
    if request.image_path is not None:
        return make_error("Screenshot Upload Not Implemented", "云端 /chat 无法读取客户端本地 image_path",
                          suggested_action="请先用文字提问；截图上传接口开放后再上传文件")
    owner = _client_id(request.client_id) if request.client_id else None
    target = _conversation_id(request.conversation_id) if request.conversation_id else None
    if target and not owner:
        raise HTTPException(status_code=422, detail="conversation_id 需要 client_id")
    if not database_configured():
        target = None
    if target and database_configured():
        try:
            if not get_conversation(target, owner):
                raise HTTPException(status_code=404, detail="未找到对话")
        except HTTPException:
            raise
        except Exception as error:
            logger.warning("chat_history_lookup_failed exception_type=%s", type(error).__name__)
            target = None
    history_warning = None
    if owner and database_configured():
        try:
            if not target:
                title = " ".join(request.message.split())[:40]
                target = create_conversation(owner, title)["id"]
            save_message(target, owner, "user", request.message)
        except Exception as error:
            logger.warning("chat_history_user_save_failed exception_type=%s", type(error).__name__)
            history_warning = "Chat History Save Failed"
    elif owner:
        history_warning = "Database Not Configured"
    result = run_ads_learning_agent(request.message)
    if owner and target and database_configured():
        try:
            tutorial = next((item for item in result.get("tool_results", [])
                             if item.get("success") and item.get("tool_name") in
                             ("get_google_ads_steps", "get_meta_ads_steps")), None)
            metadata = ({"platform": result.get("platform"), "intent": "steps",
                         "tool_name": tutorial["tool_name"], "topic": tutorial["result"].get("topic"),
                         "image_variant": tutorial["result"].get("image_variant"),
                         "steps": tutorial["result"].get("steps", [])} if tutorial else None)
            save_message(target, owner, "assistant", result.get("answer") or result.get("message") or "",
                         result.get("platform"), result.get("intent"), result.get("execution_mode"), metadata=metadata)
        except Exception as error:
            logger.warning("chat_history_assistant_save_failed exception_type=%s", type(error).__name__)
            history_warning = "Chat History Save Failed"
    if history_warning:
        result.setdefault("warnings", []).append({"error_type": history_warning, "message": "聊天记录暂时无法保存，回答仍可使用。"})
    result["conversation_id"] = target
    return result


@app.post("/analyze-screenshot", response_model=AgentResponse, response_model_exclude_unset=True)
def analyze_screenshot():
    """预留真实文件上传接口；当前不读取路径或伪造视觉结果。"""
    return make_error("Screenshot Upload Not Implemented", "当前云端版本尚未开放截图文件上传接口")


@app.post("/automation/run", response_model=AutomationResponse, response_model_exclude_unset=True)
def automation_run(request: AutomationRequest):
    """手动触发只读工作流；不影响原有 /chat。"""
    return handle_trigger(request.workflow_name, "manual", request.inputs)


@app.post("/automation/webhook/{workflow_name}", response_model=AutomationResponse,
          response_model_exclude_unset=True)
def automation_webhook(workflow_name: str, request: WebhookRequest,
                       x_automation_token: str | None = Header(default=None),
                       x_automation_trigger: str = Header(default="webhook")):
    """外部触发入口；必须提供服务端环境变量中配置的共享令牌。"""
    return handle_trigger(workflow_name, x_automation_trigger, request.inputs, x_automation_token)
