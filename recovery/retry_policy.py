"""只对明确的临时故障做有限重试。"""

import random
import time

from tools.log_tool import logger


MAX_RETRIES = 3
RETRYABLE_ERRORS = frozenset({"Timeout", "LLM Request Failed", "Search Request Failed", "Vision Request Failed"})


def retry_delay(retry_count, base_seconds=0.5, jitter=False):
    """第 1、2、3 次重试分别按指数增长，可选少量抖动。"""
    delay = min(base_seconds * (2 ** (retry_count - 1)), 8.0)
    return delay + (random.uniform(0, delay * 0.2) if jitter else 0.0)


def run_with_retry(operation, tool_name, max_retries=MAX_RETRIES, sleep_fn=time.sleep, jitter=False):
    """返回结果和实际重试次数；权限或验证错误不会重试。"""
    for retry_count in range(max_retries + 1):
        result = operation()
        if (result.get("success") is True or not result.get("retryable")
                or result.get("error_type") not in RETRYABLE_ERRORS or retry_count == max_retries):
            result.pop("retryable", None)
            return result, retry_count
        logger.warning("retry tool=%s error_type=%s retry_count=%s", tool_name, result.get("error_type"), retry_count + 1)
        sleep_fn(retry_delay(retry_count + 1, jitter=jitter))
