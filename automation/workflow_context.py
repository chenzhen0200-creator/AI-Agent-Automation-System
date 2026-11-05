"""每次自动化执行独立的上下文。"""

from datetime import datetime, timezone


def new_context(workflow_name, trigger_type, inputs):
    return {
        "workflow_name": workflow_name, "trigger_type": trigger_type,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "step_count": 0, "inputs": dict(inputs), "tool_results": [],
        "warnings": [], "status": "running", "execution_trace": ["trigger_received"],
        "retry_count": 0, "fallback_used": "none",
    }
