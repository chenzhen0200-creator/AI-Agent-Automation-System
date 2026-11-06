"""构造统一的图文式步骤结构；图片是教学界面示意。"""

import re


def topic_slug(topic):
    return re.sub(r"[^a-z0-9]+", "-", topic.casefold()).strip("-")


def attach_images(steps, platform, topic, variant=None):
    """图片由启动时的教程示意图生成器提供，不依赖真实广告账户。"""
    folder = "meta" if platform == "meta_ads" else "google"
    slug = topic_slug(variant or topic)
    for step in steps:
        step["image_url"] = f"/static/tutorial-images/{folder}/{slug}/step-{step['step_number']}.svg"
    return steps


def make_step(number, title, location, button, next_page, detail):
    """每一步都说明位置、按钮与点击后的页面。"""
    action = button if button.startswith(("查看", "核对", "展开", "返回")) else f"点击“{button}”"
    return {
        "step_number": number,
        "title": title,
        "description": detail,
        "ui_location": location,
        "action": action,
        "next_page": next_page,
        "expected_result": next_page,
        "image_hint": f"通常位于“{location}”，留意“{button}”。实际界面可能因版本而异。",
        "image_url": None,
    }
