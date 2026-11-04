"""Meta Ads 图文式操作学习步骤；不连接或修改账户。"""

from tools.visual_steps import make_step
from errors import make_error


# 每项依次为标题、界面位置、按钮、下一页面、教学说明。
ENTRY = [
    ("打开广告管理工具", "Meta Business 工具菜单", "Ads Manager／广告管理工具", "广告系列列表", "从广告管理工具学习三个层级。"),
    ("查看创建入口", "广告系列列表上方", "Create／创建", "新建广告系列向导", "只学习界面流程，不提交或发布广告。"),
]

TOPIC_STEPS = {
    "Campaign": ENTRY + [("查看广告系列目标", "新建广告系列向导", "Objective／目标", "目标选择页", "学习广告系列层级的目标设置。")],
    "Ad Set": [("进入广告组", "广告管理工具顶部层级切换", "Ad sets／广告组", "广告组列表", "广告组承载受众、版位和优化等设置。"), ("查看广告组详情", "广告组列表", "广告组名称", "广告组编辑页", "学习转化位置、排期和投放设置。")],
    "Ad": [("进入广告", "广告管理工具顶部层级切换", "Ads／广告", "广告列表", "单条广告承载创意和链接。"), ("查看广告详情", "广告列表", "广告名称", "广告编辑页", "学习素材、文案和预览。")],
    "Objective": ENTRY + [("查看目标", "新建广告系列向导", "Objective／目标", "目标选择页", "比较不同目标对应的优化结果。")],
    "Audience": [("进入广告组", "广告管理工具顶部层级切换", "Ad sets／广告组", "广告组列表", "先选一个学习示例。"), ("查看受众", "广告组编辑页", "Audience／受众", "受众设置区域", "学习地区、年龄和受众信号。")],
    "Placement": [("进入广告组", "广告管理工具顶部层级切换", "Ad sets／广告组", "广告组列表", "版位通常位于广告组层级。"), ("查看版位", "广告组编辑页", "Placements／版位", "版位设置区域", "比较自动与手动版位。")],
    "Budget": [("进入广告系列", "广告管理工具顶部层级切换", "Campaigns／广告系列", "广告系列列表", "预算可能出现在不同层级，依所选目标与设置而定。"), ("查看预算", "广告系列或广告组编辑页", "Budget & schedule／预算与排期", "预算与排期设置区域", "只学习预算类型，不改变真实金额。")],
    "Optimization": [("进入广告组", "广告管理工具顶部层级切换", "Ad sets／广告组", "广告组列表", "优化目标通常与广告组设置相关。"), ("查看优化设置", "广告组编辑页", "Optimization & delivery／优化与投放", "优化设置区域", "学习事件与目标如何对应。")],
    "Pixel": [("打开事件管理工具", "Meta Business 工具菜单", "Events Manager／事件管理工具", "数据源概览页", "这里学习网站事件的数据源。"), ("查看 Pixel", "数据源概览页", "Pixel／像素", "Pixel 事件详情页", "学习事件是否正常回传。")],
    "CAPI": [("打开事件管理工具", "Meta Business 工具菜单", "Events Manager／事件管理工具", "数据源概览页", "先确认对应的数据源。"), ("查看服务器事件", "数据源详情页", "Settings／设置", "事件连接设置页", "学习 Conversions API 与事件去重，不在此连接服务器。")],
    "Conversion Event": [("打开事件管理工具", "Meta Business 工具菜单", "Events Manager／事件管理工具", "数据源概览页", "先定位对应的 Pixel 或数据源。"), ("查看事件", "数据源详情页", "Overview／概览", "事件概览页", "学习转化事件名称与状态。")],
    "Attribution": [("进入广告组", "广告管理工具顶部层级切换", "Ad sets／广告组", "广告组列表", "先选一个学习示例。"), ("查看归因设置", "广告组编辑页", "Attribution setting／归因设置", "归因设置区域", "学习报告窗口与转化口径。")],
    "Creative": [("进入广告", "广告管理工具顶部层级切换", "Ads／广告", "广告列表", "素材位于单条广告层级。"), ("查看创意", "广告编辑页", "Ad creative／广告创意", "素材编辑与预览区域", "学习图片、视频、文案和版位预览。")],
}

ALIASES = {
    "Campaign": ("campaign", "广告系列"), "Ad Set": ("ad set", "广告组"), "Ad": ("单条广告", "广告层级", "广告列表", "里的 ad", "的 ad", " ad 在哪里"),
    "Objective": ("objective", "目标"), "Audience": ("audience", "受众"), "Placement": ("placement", "版位"),
    "Budget": ("budget", "预算"), "Optimization": ("optimization", "优化"), "Pixel": ("pixel", "像素"),
    "CAPI": ("capi", "conversions api"), "Conversion Event": ("conversion event", "转化事件"),
    "Attribution": ("attribution", "归因"), "Creative": ("creative", "素材", "创意"),
}

PRIORITY = ("CAPI", "Conversion Event", "Ad Set", "Creative", "Attribution", "Optimization", "Placement", "Audience", "Budget", "Pixel", "Objective", "Ad", "Campaign")


def get_meta_ads_steps(user_goal, screenshot=None):
    """返回分步骤说明；截图参数为未来视觉工具预留。"""
    if screenshot is not None:
        return make_error("Vision Not Configured", "当前未配置视觉模型，请用文字描述当前页面")
    text = user_goal.lower()
    topic = next((name for name in PRIORITY if any(word in text for word in ALIASES[name])), "Campaign")
    steps = [make_step(number, *item) for number, item in enumerate(TOPIC_STEPS[topic], 1)]
    return {"success": True, "platform": "meta_ads", "topic": topic, "mode": "visual_step_by_step", "presentation": "图文式步骤说明（暂无真实截图）", "steps": steps}
