"""Web API 的请求与统一结构化响应。"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """目前只接受文字；image_path 仅为兼容旧接口保留。"""

    message: str = Field(min_length=1, max_length=4000)
    image_path: str | None = None


class AgentResponse(BaseModel):
    """保留 Agent 的完整结构，避免 API 层丢失 Tool 结果或执行轨迹。"""

    model_config = ConfigDict(extra="allow")

    success: bool
    execution_mode: str | None = None
    platform: str | None = None
    intent: str | None = None
    answer: str | None = None
    tool_results: list[dict[str, Any]] | None = None
    memory_saved: bool | None = None
    sources: list[dict[str, Any]] | None = None
    warnings: list[dict[str, Any]] | None = None
    execution_trace: list[str] | None = None
    error_type: str | None = None
    message: str | None = None
    recoverable: bool | None = None
    suggested_action: str | None = None


class AutomationRequest(BaseModel):
    """手动运行一个已注册的自动化工作流。"""

    workflow_name: str = Field(min_length=1, max_length=80)
    inputs: dict[str, Any] = Field(default_factory=dict)


class WebhookRequest(BaseModel):
    """未来由外部事件或定时器提交的结构化输入。"""

    inputs: dict[str, Any] = Field(default_factory=dict)


class AutomationResponse(BaseModel):
    """保留工作流输出和统一错误字段。"""

    model_config = ConfigDict(extra="allow")
    success: bool
    workflow_name: str | None = None
    trigger_type: str | None = None
    status: str | None = None
    steps_executed: int | None = None
    results: list[dict[str, Any]] | None = None
    warnings: list[dict[str, Any]] | None = None
    execution_trace: list[str] | None = None
    error_type: str | None = None
    message: str | None = None
    recoverable: bool | None = None
    suggested_action: str | None = None
