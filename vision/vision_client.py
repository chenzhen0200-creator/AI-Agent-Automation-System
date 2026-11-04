"""视觉模型的统一入口；当前没有绑定真实服务。"""

from pathlib import Path

from config import VISION_ENABLED, VISION_MODEL_NAME
from errors import make_error
from recovery.retry_policy import run_with_retry


SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def analyze_image(image_path, prompt, adapter=None):
    """将图片和提示交给未来的视觉适配器，不包含广告业务规则。"""
    if not VISION_ENABLED or not VISION_MODEL_NAME or adapter is None:
        return make_error("Vision Not Configured", "当前未配置视觉模型，无法识别截图")
    if not isinstance(image_path, str) or not image_path.strip() or not isinstance(prompt, str) or not prompt.strip():
        return make_error("Invalid Screenshot", "截图路径或分析提示无效")
    path = Path(image_path)
    try:
        if (path.suffix.lower() not in SUPPORTED_SUFFIXES or not path.is_file()
                or not 0 < path.stat().st_size <= MAX_IMAGE_BYTES):
            return make_error("Invalid Screenshot", "请提供不超过 10 MB 的 PNG、JPEG 或 WebP 图片")
        with path.open("rb") as image_file:
            header = image_file.read(12)
        is_image = (header.startswith(b"\x89PNG\r\n\x1a\n") or header.startswith(b"\xff\xd8\xff")
                    or (header.startswith(b"RIFF") and header[8:12] == b"WEBP"))
        if not is_image:
            return make_error("Invalid Screenshot", "文件内容不是支持的图片格式")
    except OSError:
        return make_error("Invalid Screenshot", "无法读取截图文件")
    def request_once():
        try:
            return {"success": True, "payload": adapter(path, prompt)}
        except TimeoutError:
            return make_error("Vision Request Failed", "视觉模型请求超时", retryable=True)
        except Exception:
            # 不记录原图、路径、模型原始响应或账户字段。
            return make_error("Vision Request Failed", "视觉模型请求失败")

    response, retry_count = run_with_retry(request_once, "analyze_ads_screenshot")
    if not response["success"]:
        response["retry_count"] = retry_count
        return response
    result = response["payload"]
    if not isinstance(result, dict) or not isinstance(result.get("observation"), dict) or result.get("success") is not True:
        return make_error("Vision Request Failed", "视觉模型未返回有效结构", retry_count=retry_count)
    return {"success": True, "observation": result["observation"], "retry_count": retry_count}
