"""Meta Ads 图文式操作学习步骤；不连接或修改账户。"""

from tools.visual_steps import make_step, attach_images
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

# 先定位账户与目标层级，再按主题阅读设置；所有步骤均为只读教学。
OPEN_MANAGER = ("打开 Ads Manager", "Meta Business 工具菜单", "Ads Manager／广告管理工具", "广告系列列表", "确认正在查看正确的广告账户；界面名称可能因版本略有不同。")
SELECT_CAMPAIGN = ("选择目标广告系列", "Campaigns／广告系列列表", "目标 Campaign 名称", "目标广告系列详情", "确认广告系列名称与学习目标一致，不保存或发布任何更改。")
SELECT_AD_SET = ("选择目标广告组", "Ad sets／广告组列表", "目标 Ad Set 名称", "广告组详情或编辑界面", "确认该广告组属于目标广告系列；仅查看设置。")
SELECT_AD = ("选择目标广告", "Ads／广告列表", "目标 Ad 名称", "广告详情或编辑界面", "确认广告所属广告组，并查看预览。")
READ_ONLY = ("核对并退出", "当前设置界面", "返回列表／关闭编辑器", "返回列表且没有提交更改", "记录看到的设置；不要点击 Publish／发布或提交真实账户修改。")

TOPIC_STEPS["Campaign"] = [OPEN_MANAGER] + TOPIC_STEPS["Campaign"][1:] + [
    ("比较目标选项", "目标选择页", "查看各 Objective／目标说明", "理解目标与优化结果的对应关系", "目标会影响后续可选设置；当前只做教学浏览。"),
    ("查看系列层级设置", "广告系列编辑界面", "查看 Campaign details／广告系列详情", "看到系列名称与相关设置", "如界面提供特殊广告类别或系列预算，也一并识别其位置。"),
    ("核对结构", "编辑界面层级导航", "查看 Ad sets／广告组与 Ads／广告", "理解三层结构", "广告系列负责总体目标，广告组与广告分别承载投放条件和素材。"), READ_ONLY]
TOPIC_STEPS["Ad Set"] = [OPEN_MANAGER, SELECT_CAMPAIGN, ("切换到广告组", "页面顶部层级切换区", "Ad sets／广告组", "广告组列表", "此处列出所选广告系列的广告组。"), SELECT_AD_SET,
    ("查看转化位置", "广告组编辑界面上部", "查看 Conversion location／转化位置", "看到转化位置设置", "确认目标对应的网站、应用或其他转化位置。"),
    ("查看预算与排期", "广告组编辑界面", "查看 Budget & schedule／预算与排期", "看到预算和日期区域", "系列预算启用时，预算可能位于广告系列层级。"),
    ("查看受众", "广告组编辑界面", "查看 Audience／受众", "看到受众区域", "核对地区、年龄和受众设置。"),
    ("查看版位", "广告组编辑界面", "查看 Placements／版位", "看到版位区域", "识别自动版位和可用的手动版位。"),
    ("查看优化与投放", "广告组编辑界面下部", "查看 Optimization & delivery／优化与投放", "看到优化设置", "核对优化事件和投放选项。"), READ_ONLY]
TOPIC_STEPS["Ad"] = [OPEN_MANAGER, ("切换到广告", "页面顶部层级切换区", "Ads／广告", "广告列表", "这里显示单条广告。"), SELECT_CAMPAIGN, SELECT_AD_SET, SELECT_AD,
    ("查看广告创意", "广告编辑界面", "查看 Ad creative／广告创意", "看到素材与文案", "检查图片或视频、正文、标题等字段。"),
    ("查看预览", "广告编辑界面预览区", "查看 Preview／预览", "看到不同版位预览", "预览只用于学习，不发布。"), READ_ONLY]
TOPIC_STEPS["Objective"] = [OPEN_MANAGER] + TOPIC_STEPS["Objective"][1:] + [
    ("比较可选目标", "目标选择页", "查看各 Objective／目标说明", "看到目标简介", "将业务目标与目标类型对应，不必真的创建。"),
    ("查看后续层级", "创建向导的层级导航", "查看 Ad set／广告组设置", "理解目标如何影响后续选项", "不同目标的转化位置与优化项可能不同。"), READ_ONLY]
TOPIC_STEPS["Audience"] = [OPEN_MANAGER, SELECT_CAMPAIGN, SELECT_AD_SET] + TOPIC_STEPS["Audience"][1:] + [
    ("查看基本条件", "Audience／受众区域", "查看 Locations／地区与 Age／年龄", "看到地域和年龄条件", "这些条件决定可覆盖的人群。"),
    ("查看自定义受众", "Audience／受众区域", "查看 Custom Audiences／自定义受众", "看到已选受众或空状态", "仅学习包含与排除设置。"),
    ("核对受众范围", "Audience／受众区域附近", "查看受众规模提示", "理解潜在覆盖范围", "规模提示是估计值，界面可能因版本而异。"), READ_ONLY]
TOPIC_STEPS["Placement"] = [OPEN_MANAGER, SELECT_CAMPAIGN, SELECT_AD_SET] + TOPIC_STEPS["Placement"][1:] + [
    ("比较版位方式", "Placements／版位区域", "查看 Advantage+ placements 与手动版位", "看到可用版位方式", "仅比较差异，不切换真实投放。"),
    ("查看渠道列表", "版位设置区域", "展开可用平台与位置", "看到 Feed、Stories 等可用位置", "可用位置取决于目标与素材。"),
    ("核对素材适配", "广告预览或版位说明区", "查看版位预览", "了解各版位展示效果", "注意画面比例与文本裁切。"), READ_ONLY]
TOPIC_STEPS["Budget"] = [OPEN_MANAGER, SELECT_CAMPAIGN] + TOPIC_STEPS["Budget"][1:] + [
    ("确认预算层级", "广告系列与广告组编辑界面", "查看 Budget／预算区域", "确定预算位于系列或广告组", "系列预算启用时，广告组可能不提供独立预算字段。"),
    ("查看预算类型", "Budget & schedule／预算与排期", "查看 Daily／每日与 Lifetime／总预算说明", "理解预算类型", "仅阅读当前金额，不修改。"),
    ("查看排期", "Budget & schedule／预算与排期", "查看开始和结束日期", "看到投放时间范围", "排期可能影响花费节奏。"), READ_ONLY]
TOPIC_STEPS["Optimization"] = [OPEN_MANAGER, SELECT_CAMPAIGN, SELECT_AD_SET] + TOPIC_STEPS["Optimization"][1:] + [
    ("核对优化事件", "Optimization & delivery／优化与投放", "查看 Performance goal／成效目标", "看到目标与优化事件", "确认事件和广告系列目标相匹配。"),
    ("查看投放方式", "同一设置区域", "查看 Delivery／投放说明", "看到可用投放选项", "选项随目标和账户配置变化。"), READ_ONLY]
TOPIC_STEPS["Pixel"] = [OPEN_MANAGER] + TOPIC_STEPS["Pixel"] + [
    ("选择数据源", "Events Manager／事件管理工具", "目标 Pixel／数据集", "数据源详情页", "确认数据源属于当前学习示例。"),
    ("查看事件状态", "数据源概览或测试事件页", "查看 Overview／概览", "看到最近事件与状态", "留意最近接收时间和诊断提示。"),
    ("查看设置说明", "数据源详情的 Settings／设置", "查看 Pixel 设置", "看到连接与配置说明", "这里只阅读，不安装代码或连接真实站点。"), READ_ONLY]
TOPIC_STEPS["CAPI"] = [OPEN_MANAGER] + TOPIC_STEPS["CAPI"] + [
    ("选择数据源", "Events Manager／事件管理工具", "目标数据集／Pixel", "数据源详情页", "确认正在查看需要学习的数据源。"),
    ("查看连接方式", "Settings／设置区域", "查看 Conversions API 连接说明", "看到服务器事件配置说明", "当前只解释配置路径，不生成或提交访问令牌。"),
    ("查看事件去重", "事件详情或诊断区域", "查看 Event ID／事件 ID 与诊断", "理解浏览器与服务器事件去重", "重复事件可能影响统计，应按官方文档核对。"), READ_ONLY]
TOPIC_STEPS["Conversion Event"] = [OPEN_MANAGER] + TOPIC_STEPS["Conversion Event"] + [
    ("选择数据源", "Events Manager 数据源列表", "目标数据集／Pixel", "事件概览页", "确认要学习的网站或应用数据源。"),
    ("查看事件名称", "Overview／概览中的事件列表", "查看 Purchase／购买等事件", "看到事件详情", "比较事件名称、来源与最近接收时间。"),
    ("查看诊断", "事件详情", "查看 Diagnostics／诊断", "看到警告或正常状态", "若有警告，先记录内容再查官方资料。"), READ_ONLY]
TOPIC_STEPS["Attribution"] = [OPEN_MANAGER, SELECT_CAMPAIGN, SELECT_AD_SET] + TOPIC_STEPS["Attribution"][1:] + [
    ("查看归因窗口", "Attribution setting／归因设置", "查看可用窗口说明", "理解点击和浏览归因窗口", "可用窗口随目标变化；不要假定所有账户相同。"),
    ("核对报告口径", "Ads Manager 报表设置", "查看 Columns／列和归因说明", "理解报表指标口径", "比较数据前应确认使用同一归因设置。"), READ_ONLY]
TOPIC_STEPS["Creative"] = [OPEN_MANAGER, SELECT_CAMPAIGN, SELECT_AD_SET, SELECT_AD] + TOPIC_STEPS["Creative"][1:] + [
    ("查看素材字段", "Ad creative／广告创意", "查看图片／视频与正文／标题", "看到广告素材字段", "只观察内容，不上传或保存素材。"),
    ("查看版位预览", "广告编辑界面预览区域", "查看 Preview／预览", "看到不同版位效果", "检查画面比例、裁切和文案可读性。"), READ_ONLY]

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
    items = TOPIC_STEPS[topic]
    duplicate = topic == "Ad Set" and any(word in text for word in ("复制", "duplicate", "copy"))
    if duplicate:
        items = [OPEN_MANAGER, SELECT_CAMPAIGN,
            ("切换到广告组", "顶部层级切换区", "Ad sets／广告组", "所选系列的广告组列表", "确认目标 Campaign 与原广告组。"),
            ("选择来源广告组", "广告组列表", "查看原 Ad Set 名称与勾选框", "来源广告组已定位", "核对受众、版位和排期，避免误选。"),
            ("查看复制入口", "广告组列表上方或行操作菜单", "查看 Duplicate／复制", "复制设置界面", "入口通常位于操作栏；当前界面可能因账户版本略有不同。只做教学演示。"),
            ("查看复制目标", "复制设置界面", "查看目标 Campaign 与副本数量", "看到复制目标选项", "若要在同一系列复制，目标应指向当前 Campaign；不要确认执行。"),
            ("核对副本设置", "复制预览或编辑界面", "查看受众、预算、版位和优化", "理解副本继承的设置", "复制后仍需逐项核对，当前不提交。"), READ_ONLY]
    steps = attach_images([make_step(number, *item) for number, item in enumerate(items, 1)], "meta_ads", topic, "Ad Set Duplicate" if duplicate else None)
    return {"success": True, "platform": "meta_ads", "topic": topic,
            "image_variant": "Ad Set Duplicate" if duplicate else None,
            "mode": "visual_step_by_step", "presentation": "分步骤教学；有已核实截图时显示图片", "steps": steps}
