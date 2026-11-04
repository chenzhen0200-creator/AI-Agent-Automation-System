"""把 API 数据转换为可直接展示的任务结果。"""

from datetime import datetime

from tools.api_tool import fetch_task
from tools.log_tool import logger
from errors import make_error


def run_task_workflow():
    """执行工作流，返回包含成功状态和任务信息的字典。"""
    logger.info("状态工作流开始，时间：%s", datetime.now().astimezone().isoformat(timespec="seconds"))
    api_result = fetch_task()
    if not api_result["ok"]:
        # API 工具已经区分错误类型，工作流记录后原样传给入口。
        logger.error("API 请求失败：%s：%s", api_result["error_type"], api_result["message"])
        return make_error(api_result["error_type"], api_result["message"])

    logger.info("API 请求成功")

    data = api_result["data"]
    try:
        # 工作流需要这三个字段；缺少字段时给出友好提示。
        task_id = data["id"]
        title = data["title"]
        completed = data["completed"]
    except (KeyError, TypeError) as error:
        message = f"缺少必需字段或数据格式不正确（{error}）。"
        logger.error("Missing Field：%s", message)
        return make_error("Missing Field", message)

    # 根据 completed 的值生成最终状态。
    status = "任务已完成" if completed else "任务未完成"
    logger.info("completed 判断结果：%s；%s", completed, status)
    return {
        "success": True,
        "task_id": task_id,
        "title": title,
        "completed": completed,
        "message": status,
    }
