"""获取测试任务的 ID 和标题。"""

from datetime import datetime

from tools.api_tool import fetch_task
from tools.log_tool import logger
from errors import make_error


def run_title_workflow():
    """复用 API 工具，只提取标题查询需要的两个字段。"""
    logger.info("标题工作流开始，时间：%s", datetime.now().astimezone().isoformat(timespec="seconds"))
    api_result = fetch_task()
    if not api_result["ok"]:
        logger.error("API 请求失败：%s：%s", api_result["error_type"], api_result["message"])
        return make_error(api_result["error_type"], api_result["message"])

    logger.info("API 请求成功")
    try:
        # 标题查询不需要 completed，因此只检查 id 和 title。
        task_id = api_result["data"]["id"]
        title = api_result["data"]["title"]
    except (KeyError, TypeError) as error:
        message = f"缺少必需字段或数据格式不正确（{error}）。"
        logger.error("Missing Field：%s", message)
        return make_error("Missing Field", message)

    logger.info("已获取任务标题：ID=%s", task_id)
    return {"success": True, "task_id": task_id, "title": title}
