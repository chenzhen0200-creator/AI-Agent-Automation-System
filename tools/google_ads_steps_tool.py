"""Google Ads 图文式操作学习步骤；不连接或修改账户。"""

from tools.visual_steps import make_step
from errors import make_error


# 每项依次为标题、界面位置、按钮、下一页面、教学说明。
CAMPAIGN_ENTRY = [
    ("进入广告系列", "Google Ads 左侧导航栏", "Campaigns／广告系列", "广告系列列表", "先找到广告系列入口。"),
    ("打开新建向导", "广告系列列表上方", "Create／创建", "创建菜单", "在列表页查看新建入口，不必真正提交广告。"),
    ("选择新建广告系列", "创建菜单", "Campaign／广告系列", "广告系列目标与类型页", "先理解目标，再选择广告类型。"),
]

TOPIC_STEPS = {
    "Campaign": CAMPAIGN_ENTRY,
    "Ad Group": [("打开广告组", "左侧 Campaigns／广告系列菜单", "Ad groups／广告组", "广告组列表", "广告组用于组织相关广告及定向。"), ("查看广告组设置", "广告组列表", "广告组名称", "广告组详情页", "在详情页学习受众、关键词等设置。")],
    "Ads": [("打开广告", "左侧 Campaigns／广告系列菜单", "Ads／广告", "广告列表", "这里集中查看广告素材。"), ("查看广告详情", "广告列表", "广告名称", "广告详情页", "核对标题、素材和落地页。")],
    "Keywords": [("打开关键词", "左侧 Audiences, keywords and content／受众、关键词和内容菜单", "Keywords／关键词", "关键词列表", "搜索广告的关键词通常按广告组管理。"), ("查看添加入口", "关键词列表上方", "+／添加", "选择广告组窗口", "先选目标广告组，再学习关键词匹配。")],
    "Audiences": [("打开受众", "左侧 Audiences, keywords and content／受众、关键词和内容菜单", "Audiences／受众", "受众页面", "先区分定向和观察用途。"), ("查看细分", "受众页面", "Edit audience／编辑受众", "受众编辑面板", "学习受众信号和排除设置。")],
    "Budget": [("进入广告系列", "左侧导航栏", "Campaigns／广告系列", "广告系列列表", "预算通常与广告系列相关。"), ("查看预算", "广告系列列表", "Budget／预算列", "预算设置视图", "只阅读日预算含义，不更改真实金额。")],
    "Bidding": [("进入广告系列", "左侧导航栏", "Campaigns／广告系列", "广告系列列表", "先选择要学习的系列。"), ("查看出价", "广告系列详情的 Settings／设置", "Bidding／出价", "出价设置区域", "比较不同目标对应的出价策略。")],
    "Locations": [("进入广告系列", "左侧导航栏", "Campaigns／广告系列", "广告系列列表", "先选择要学习的系列。"), ("查看地域", "广告系列详情的 Settings／设置", "Locations／地理位置", "地理位置设置区域", "学习目标地域与排除地域。")],
    "Conversion": [("打开目标", "Google Ads 左侧导航栏", "Goals／目标", "目标菜单", "先找到转化设置入口。"), ("查看转化", "目标菜单", "Conversions／转化", "转化概览页", "学习转化动作和记录状态。")],
    "Search": CAMPAIGN_ENTRY + [("选择搜索广告", "广告系列目标与类型页", "Search／搜索", "搜索广告系列设置页", "学习关键词、广告组和搜索广告的关系。")],
    "Video / YouTube": CAMPAIGN_ENTRY + [("选择视频广告", "广告系列目标与类型页", "Video／视频", "视频广告系列设置页", "学习视频素材、目标和受众。")],
    "Performance Max": CAMPAIGN_ENTRY + [("选择 PMax", "广告系列目标与类型页", "Performance Max", "Performance Max 设置页", "学习转化目标、素材组和受众信号。")],
    "Demand Gen": CAMPAIGN_ENTRY + [("选择 Demand Gen", "广告系列目标与类型页", "Demand Gen", "Demand Gen 设置页", "学习素材、受众与出价。")],
    "Display": CAMPAIGN_ENTRY + [("选择展示广告", "广告系列目标与类型页", "Display／展示", "展示广告系列设置页", "学习受众、素材和内容设置。")],
    "Shopping": CAMPAIGN_ENTRY + [("选择购物广告", "广告系列目标与类型页", "Shopping／购物", "购物广告系列设置页", "学习商品数据源和商品覆盖。")],
}

ALIASES = {
    "Campaign": ("campaign", "广告系列"), "Ad Group": ("ad group", "广告组"), "Ads": ("广告文案", "广告素材", "ads 页面", "广告列表", "广告层级", "里的 ads", "的 ads"),
    "Keywords": ("keywords", "keyword", "关键词"), "Audiences": ("audience", "受众"), "Budget": ("budget", "预算"),
    "Bidding": ("bidding", "出价"), "Locations": ("locations", "地域", "地理位置"), "Conversion": ("conversion", "转化追踪", "转化设置"),
    "Search": ("search", "搜索广告"), "Video / YouTube": ("youtube", "video", "视频广告"),
    "Performance Max": ("performance max", "pmax"), "Demand Gen": ("demand gen",), "Display": ("display", "展示广告"), "Shopping": ("shopping", "购物广告"),
}

PRIORITY = ("Performance Max", "Demand Gen", "Video / YouTube", "Shopping", "Display", "Search", "Ad Group", "Keywords", "Audiences", "Budget", "Bidding", "Locations", "Conversion", "Ads", "Campaign")


def get_google_ads_steps(user_goal, screenshot=None):
    """返回分步骤说明；截图参数为未来视觉工具预留。"""
    if screenshot is not None:
        return make_error("Vision Not Configured", "当前未配置视觉模型，请用文字描述当前页面")
    text = user_goal.lower()
    topic = next((name for name in PRIORITY if any(word in text for word in ALIASES[name])), "Campaign")
    steps = [make_step(number, *item) for number, item in enumerate(TOPIC_STEPS[topic], 1)]
    return {"success": True, "platform": "google_ads", "topic": topic, "mode": "visual_step_by_step", "presentation": "图文式步骤说明（暂无真实截图）", "steps": steps}
