"""构造统一步骤，并且只关联已登记的真实后台截图。"""

from tools.tutorial_screenshots import screenshots_for


def attach_images(steps, platform, topic, variant=None):
    """未核实的图片一律不返回；旧版模拟图片 URL 也会被清除。"""
    screenshots = screenshots_for(platform, topic, variant)
    for step in steps:
        step.update({"image_url": None, "image_type": None, "image_source": None,
                     "source_url": None, "captured_at": None, "platform": platform})
        step.update(screenshots.get(step.get("step_number"), {}))
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
        "image_type": None,
        "image_source": None,
        "source_url": None,
        "captured_at": None,
    }
