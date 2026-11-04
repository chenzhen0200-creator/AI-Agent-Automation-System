"""将视觉模型的观察转换为广告后台页面分析。"""

from vision.ui_element_parser import parse_ui_elements
from vision.vision_client import analyze_image
from errors import make_error


MIN_CONFIDENCE = 0.70
GOOGLE_PAGES = {
    "campaigns": "campaign", "ad groups": "ad_group", "ads": "ad", "keywords": "keyword",
    "search terms": "search_term", "audiences": "audience", "locations": "location",
    "budget": "budget", "bidding": "bidding", "conversions": "conversion",
    "video campaign": "video_campaign", "performance max": "performance_max", "demand gen": "demand_gen",
}
META_PAGES = {
    "campaign": "campaign", "campaigns": "campaign", "ad set": "ad_set", "ad sets": "ad_set",
    "ad": "ad", "ads": "ad", "audience": "audience", "placements": "placement",
    "budget": "budget", "optimization": "optimization", "pixel": "pixel",
    "events manager": "events_manager", "attribution": "attribution", "creative": "creative",
    "delivery / review status": "review_status", "review status": "review_status",
}


def _texts(items):
    if not isinstance(items, list):
        return []
    return [item.strip()[:200] for item in items if isinstance(item, str) and item.strip()][:40]


def analyze_screenshot(image_path, user_goal, platform_hint="unknown", adapter=None):
    """只信任结构化的真实视觉结果；置信度不足时停止。"""
    prompt = (
        "只分析 Google Ads 或 Meta Ads 后台截图，不执行任何点击或账户修改。"
        "返回结构化 observation：platform、current_page、confidence（0到1）、"
        "screenshot_complete、visible_navigation、elements、selected_items、warning_messages、"
        "review_status、possible_next_actions。元素含 element_type、text、location、state、confidence。"
        "看不清时标低置信度，不猜测按钮或页面。"
    )
    vision = analyze_image(image_path, prompt, adapter=adapter)
    if not vision["success"]:
        return vision
    observation = vision["observation"]
    elements = parse_ui_elements(observation)
    navigation = _texts(observation.get("visible_navigation"))
    if not navigation:
        navigation = [item["text"] for item in elements if item["element_type"] in ("menu", "tab") and item["confidence"] >= MIN_CONFIDENCE]
    if observation.get("screenshot_complete") is False or not navigation:
        return make_error("Incomplete Screenshot", "当前截图缺少导航栏或关键区域，无法确定页面位置", retry_count=vision.get("retry_count", 0))
    platform = observation.get("platform")
    page = observation.get("current_page")
    confidence = observation.get("confidence")
    if (platform not in ("google_ads", "meta_ads") or not isinstance(page, str)
            or isinstance(confidence, bool) or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1 or confidence < MIN_CONFIDENCE):
        return make_error("Low Vision Confidence", "无法可靠识别当前截图中的页面或控件，请提供更完整截图", retry_count=vision.get("retry_count", 0))
    if platform_hint in ("google_ads", "meta_ads") and platform != platform_hint:
        return make_error("Low Vision Confidence", "截图平台与问题提示不一致，请提供更完整截图", retry_count=vision.get("retry_count", 0))
    pages = GOOGLE_PAGES if platform == "google_ads" else META_PAGES
    page_level = pages.get(page.strip().lower())
    if page_level is None:
        return make_error("Low Vision Confidence", "无法可靠识别当前截图中的页面或控件，请提供更完整截图", retry_count=vision.get("retry_count", 0))
    return {
        "success": True, "platform": platform, "current_page": page.strip(), "page_level": page_level,
        "retry_count": vision.get("retry_count", 0),
        "confidence": float(confidence), "visible_navigation": navigation,
        "visible_buttons": [item for item in elements if item["element_type"] == "button"],
        "visible_fields": [item for item in elements if item["element_type"] == "field"],
        "selected_items": _texts(observation.get("selected_items")) or [item["text"] for item in elements if item["state"] == "selected"],
        "warning_messages": _texts(observation.get("warning_messages")) or [item["text"] for item in elements if item["element_type"] == "warning"],
        "review_status": observation.get("review_status") if isinstance(observation.get("review_status"), str) else None,
        "possible_next_actions": _texts(observation.get("possible_next_actions")),
        "visible_elements": elements,
    }
