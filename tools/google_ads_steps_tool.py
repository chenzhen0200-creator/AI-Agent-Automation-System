"""Google Ads 图文式操作学习步骤；不连接或修改账户。"""

from tools.visual_steps import make_step, attach_images
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

# 公共导航和主题专属检查点均为只读教学；界面可能因账户版本略有不同。
OPEN_GOOGLE = ("打开 Google Ads", "Google Ads 账户首页", "查看当前账户与左侧导航栏", "看到广告账户概览", "先确认学习示例所属账户，不执行任何发布或修改。")
SELECT_CAMPAIGN = ("选择目标广告系列", "Campaigns／广告系列列表", "目标 Campaign 名称", "广告系列详情页", "确认广告系列类型与当前学习主题一致。")
SELECT_GROUP = ("选择目标广告组", "Ad groups／广告组列表", "目标 Ad group 名称", "广告组详情页", "确认该广告组属于目标广告系列。")
EXIT = ("核对并返回", "当前设置页面", "返回列表／关闭编辑界面", "回到列表且没有提交更改", "记录设置位置；不要保存、发布或更改真实投放。")

TOPIC_STEPS["Campaign"] = [OPEN_GOOGLE] + TOPIC_STEPS["Campaign"] + [
    ("查看目标与类型", "广告系列目标与类型页", "查看目标和 Campaign type／广告系列类型", "理解不同系列的设置路径", "选项随账户与地区变化，当前仅学习。"),
    ("查看预算与出价", "广告系列设置界面", "查看 Budget／预算与 Bidding／出价", "看到预算和出价区域", "区分预算金额与出价策略，不填写真实金额。"),
    ("查看地域与受众", "广告系列设置界面", "查看 Locations／地理位置与 Audiences／受众", "看到定向区域", "不同类型的系列可用选项可能不同。"),
    ("查看广告组与广告", "设置向导的后续层级", "查看 Ad groups／广告组和 Ads／广告", "理解系列下级结构", "核对关键词或素材的设置层级。"), EXIT]
TOPIC_STEPS["Ad Group"] = [OPEN_GOOGLE, TOPIC_STEPS["Campaign"][1], SELECT_CAMPAIGN] + TOPIC_STEPS["Ad Group"] + [
    ("查看关键词或受众", "广告组详情及左侧相关导航", "查看 Keywords／关键词或 Audiences／受众", "看到该组的定向内容", "搜索广告通常查看关键词；其他系列可能以受众或信号为主。"),
    ("查看出价与关联广告", "广告组设置和 Ads／广告列表", "查看 Bidding／出价与 Ads／广告", "看到设置及下级广告", "广告组可用出价字段取决于广告系列策略。"), EXIT]
TOPIC_STEPS["Ads"] = [OPEN_GOOGLE, TOPIC_STEPS["Campaign"][1], SELECT_CAMPAIGN] + TOPIC_STEPS["Ads"] + [
    ("核对广告内容", "广告详情页", "查看标题、描述与素材", "看到广告内容", "广告类型不同，字段也不同。"),
    ("核对落地页", "广告详情页", "查看 Final URL／最终到达网址", "看到目标页面地址", "这里只做检查，不修改目标网址。"),
    ("查看预览与状态", "广告详情或列表", "查看 Preview／预览与 Status／状态", "了解呈现效果与审核状态", "审核状态和预览可能因广告类型而异。"), EXIT]
TOPIC_STEPS["Keywords"] = [OPEN_GOOGLE, TOPIC_STEPS["Campaign"][1], SELECT_CAMPAIGN, SELECT_GROUP] + TOPIC_STEPS["Keywords"] + [
    ("查看关键词字段", "关键词列表或添加界面", "查看 Keyword／关键词与 Match type／匹配类型", "理解关键词输入格式", "广泛、词组和完全匹配适用范围不同；不要提交添加。"),
    ("查看搜索词", "关键词相关导航", "查看 Search terms／搜索词", "看到搜索词报告入口", "区分用户实际搜索词与设定的关键词。"), EXIT]
TOPIC_STEPS["Audiences"] = [OPEN_GOOGLE, TOPIC_STEPS["Campaign"][1], SELECT_CAMPAIGN] + TOPIC_STEPS["Audiences"] + [
    ("核对使用层级", "受众页面顶部或范围选择区", "查看 Campaign／系列与 Ad group／广告组范围", "知道受众作用范围", "不同系列支持的受众类型不同。"),
    ("比较定向与观察", "受众编辑面板", "查看 Targeting／定向与 Observation／观察说明", "理解两种使用方式", "若界面不提供某选项，以当前系列类型为准。"),
    ("查看排除与细分", "受众编辑面板", "查看 Exclusions／排除与受众细分", "看到可用细分设置", "只读检查，不保存更改。"), EXIT]
TOPIC_STEPS["Budget"] = [OPEN_GOOGLE] + TOPIC_STEPS["Budget"] + [SELECT_CAMPAIGN,
    ("查看预算类型", "Campaign Settings／广告系列设置", "查看 Budget／预算", "看到预算金额及类型", "共享预算与单系列预算呈现位置可能不同。"),
    ("查看投放时间", "广告系列设置", "查看开始与结束日期", "看到投放排期", "排期会影响实际花费。"), EXIT]
TOPIC_STEPS["Bidding"] = [OPEN_GOOGLE] + TOPIC_STEPS["Bidding"] + [SELECT_CAMPAIGN,
    ("查看策略名称", "Bidding／出价区域", "查看当前 Bid strategy／出价策略", "看到策略与目标字段", "区分点击、转化与转化价值目标。"),
    ("查看目标值", "出价设置区域", "查看 Target CPA／目标每次转化费用或 Target ROAS／目标广告支出回报率", "看到适用的目标字段", "仅核对，不输入或更改目标值。"), EXIT]
TOPIC_STEPS["Locations"] = [OPEN_GOOGLE] + TOPIC_STEPS["Locations"] + [SELECT_CAMPAIGN,
    ("查看包含地域", "Locations／地理位置区域", "查看已定位的国家、城市或地区", "看到包含列表", "检查地域范围与学习目标是否一致。"),
    ("查看排除地域", "同一设置区域", "查看 Excluded locations／排除地域", "看到排除列表或空状态", "同时留意高级位置选项，名称可能因版本变化。"), EXIT]
TOPIC_STEPS["Conversion"] = [OPEN_GOOGLE] + TOPIC_STEPS["Conversion"] + [
    ("选择转化动作", "Conversions／转化概览页", "目标 Conversion action／转化动作", "转化动作详情", "核对来源、统计状态及主要或次要用途。"),
    ("查看诊断", "转化动作详情或 Diagnostics／诊断", "查看状态与最近活动", "看到记录状态与提示", "异常时记录警告并参考最新官方文档。"), EXIT]

# 各广告系列类型先走统一创建向导，再查看该类型专属配置。仅做演示，不提交。
CAMPAIGN_DETAILS = {
    "Search": [("查看搜索网络设置", "搜索系列设置页", "查看 Networks／网络与 Locations／地域", "看到投放范围", "确认搜索网络与地域的教学选项。"), ("查看预算和出价", "搜索系列设置页", "查看 Budget／预算与 Bidding／出价", "看到预算与策略", "不填写真实金额。"), ("查看广告组", "广告组设置页", "查看 Ad group／广告组", "看到广告组层级", "广告组组织相关关键词与广告。"), ("查看关键词与广告", "广告组和广告设置页", "查看 Keywords／关键词与 Ads／广告", "看到匹配类型与广告内容", "核对落地页、标题和描述。")],
    "Video / YouTube": [("查看视频系列设置", "视频系列设置页", "查看目标、网络与地域", "看到可用视频投放选项", "视频广告设置随目标而变。"), ("查看预算与出价", "视频系列设置页", "查看 Budget／预算与 Bidding／出价", "看到可用策略", "只解释策略，不输入金额。"), ("查看受众", "视频广告组设置页", "查看 Audiences／受众", "看到受众选项", "了解受众与内容定向。"), ("查看视频素材", "视频广告设置页", "查看 YouTube video／视频和预览", "看到素材与预览", "学习视频链接及呈现，不上传或发布。")],
    "Performance Max": [("查看转化目标", "PMax 设置页", "查看 Conversion goals／转化目标", "看到优化目标", "目标应对应业务转化。"), ("查看预算与出价", "PMax 设置页", "查看 Budget／预算与 Bidding／出价", "看到预算和策略", "不更改真实投放。"), ("查看素材资源组", "Asset groups／素材资源组", "查看文字、图片和视频素材", "看到素材构成", "不同资源用于不同展示位置。"), ("查看受众信号", "素材资源组设置页", "查看 Audience signals／受众信号", "看到信号区域", "信号用于学习算法，不等于严格受众限制。")],
    "Demand Gen": [("查看系列设置", "Demand Gen 设置页", "查看目标、地域与语言", "看到基础设置", "可用选项依账户而异。"), ("查看预算与出价", "Demand Gen 设置页", "查看 Budget／预算与 Bidding／出价", "看到策略选项", "只阅读不修改。"), ("查看受众", "广告组设置页", "查看 Audiences／受众", "看到受众细分", "了解可用信号与排除。"), ("查看素材与预览", "广告设置页", "查看图片、视频与预览", "看到展示形式", "核对素材与投放位置的适配。")],
    "Display": [("查看投放范围", "展示系列设置页", "查看地域、语言与网络设置", "看到展示范围", "不同目标可用选项不同。"), ("查看预算与出价", "展示系列设置页", "查看 Budget／预算与 Bidding／出价", "看到预算与策略", "不输入金额。"), ("查看受众与内容", "广告组设置页", "查看 Audiences／受众与 Content／内容", "看到定向选项", "区分人群与内容定向。"), ("查看响应式素材", "广告设置页", "查看图片、标题和描述", "看到素材预览", "学习素材组合与展示位置。")],
    "Shopping": [("查看商品数据来源", "购物系列设置页", "查看 Merchant Center／商家中心关联", "看到商品数据来源", "仅核对关联状态，不连接新账户。"), ("查看国家与商品范围", "购物系列设置页", "查看销售国家与商品选项", "看到商品覆盖范围", "商品是否可用取决于数据源。"), ("查看预算与出价", "购物系列设置页", "查看 Budget／预算与 Bidding／出价", "看到策略与预算", "只阅读，不更改。"), ("查看商品组", "广告组或商品组页面", "查看 Product groups／商品组", "看到商品分组", "理解分组对商品覆盖和报告的影响。")],
}
for campaign_type, details in CAMPAIGN_DETAILS.items():
    TOPIC_STEPS[campaign_type] = [OPEN_GOOGLE] + TOPIC_STEPS[campaign_type] + details + [EXIT]

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
    steps = attach_images([make_step(number, *item) for number, item in enumerate(TOPIC_STEPS[topic], 1)], "google_ads", topic)
    return {"success": True, "platform": "google_ads", "topic": topic, "mode": "visual_step_by_step", "presentation": "图文式步骤说明（暂无真实截图）", "steps": steps}
