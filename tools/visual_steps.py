"""构造统一的图文式步骤结构；当前没有真实截图。"""


def make_step(number, title, location, button, next_page, detail):
    """每一步都说明位置、按钮与点击后的页面。"""
    return {
        "step_number": number,
        "title": title,
        "description": f"{detail} 点击“{button}”后进入“{next_page}”。",
        "ui_location": location,
        "action": f"点击“{button}”",
        "next_page": next_page,
        "image_hint": f"未来截图应标出“{location}”中的“{button}”，并展示随后出现的“{next_page}”。",
    }
