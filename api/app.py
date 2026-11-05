"""云端 FastAPI 入口；CLI 仍由 main.py 提供。"""

import traceback
import os
from pathlib import Path

from fastapi import FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from agents.ads_learning_agent import run_ads_learning_agent
from api.schemas import AgentResponse, AutomationRequest, AutomationResponse, ChatRequest, WebhookRequest
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
            "vision_enabled": VISION_ENABLED, "search_configured": bool(os.getenv(SEARCH_API_KEY_ENV_NAME))}


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
    return run_ads_learning_agent(request.message)


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
