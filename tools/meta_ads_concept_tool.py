"""Meta Ads 概念解释：与 Google 工具使用相同的结果字段。"""

from tools.learning_content import find_topic


# 英文名、中文名、解释、公式、学习价值、示例。
TOPICS = {
    "Campaign": ("Campaign", "广告系列", "确定营销目标的上层结构。", None, "帮助区分广告系列与广告组职责。", "一个销售目标广告系列包含多个广告组。"),
    "Ad Set": ("Ad Set", "广告组", "承载受众、版位、排期及优化等设置的层级，具体选项依目标而变。", None, "定位投放条件。", "同一系列下设置不同受众的广告组。"),
    "Ad": ("Ad", "广告", "承载素材、文案、链接和预览的层级。", None, "学习创意如何影响点击和转化。", "一条广告使用一张图片和一段文案。"),
    "CPM": ("Cost per Mille", "千次展示费用", "每千次展示的平均费用。", "Cost / Impressions × 1000", "观察曝光成本。", "花费 20 元获得 2000 次展示，CPM 为 10 元。"),
    "CPC": ("Cost per Click", "每次点击费用", "广告费用除以所选点击指标的次数。", "Cost / Clicks", "观察获得点击的成本。", "花费 100 元获得 50 次所选点击，CPC 为 2 元。"),
    "CTR": ("Click-Through Rate", "点击率", "所选点击指标占展示次数的比例。", "Clicks / Impressions × 100%", "观察素材与受众的相关性。", "100 次展示获得 5 次所选点击，CTR 为 5%。"),
    "CPA": ("Cost per Action", "每次行动费用", "广告费用除以所选行动的次数。", "Cost / Actions", "衡量获取目标行动的成本。", "花费 200 元获得 10 次购买，CPA 为 20 元。"),
    "ROAS": ("Return on Ad Spend", "广告支出回报", "归因转化价值与广告费用之比。", "Attributed Revenue / Cost", "比较记录到的价值与广告费用。", "花费 100 元、归因收入 400 元，ROAS 为 4。"),
    "Pixel": ("Meta Pixel", "Meta 像素", "网站端发送用户行为事件的方式。", None, "帮助理解网站行为衡量。", "商品详情页触发 ViewContent 事件。"),
    "CAPI": ("Conversions API", "转化 API", "通过服务器端向 Meta 发送事件的方式。", None, "学习服务器事件与浏览器事件的配合及去重。", "服务器发送 Purchase 事件，并与 Pixel 事件去重。"),
    "Conversion Event": ("Conversion Event", "转化事件", "用来表示特定行动的事件，例如购买或提交线索。", None, "决定广告优化和报告关注的行动。", "购买完成时记录 Purchase 事件。"),
    "Audience": ("Audience", "受众", "广告计划触达的人群或系统使用的人群信号。", None, "帮助理解覆盖规模。", "以特定地区的人群作为学习示例。"),
    "Custom Audience": ("Custom Audience", "自定义受众", "根据已有互动或获准使用的数据建立的受众。", None, "学习再营销与数据使用边界。", "用网站访问者构建示例受众。"),
    "Lookalike Audience": ("Lookalike Audience", "类似受众", "依据来源受众寻找特征相近的人群。", None, "理解来源质量与拓展范围。", "以高质量购买者受众作为来源。"),
    "Placement": ("Placement", "版位", "广告可展示的位置。", None, "帮助判断素材适配。", "比较 Feed 与 Stories 的素材预览。"),
    "Advantage+ Placements": ("Advantage+ Placements", "Advantage+ 版位", "由系统在可用版位中分配展示的自动版位选项。", None, "理解自动分配与素材适配。", "检查不同版位的预览。"),
    "Optimization": ("Optimization", "优化", "选择系统要争取的结果或事件。", None, "让衡量目标与学习目标一致。", "以购买事件作为转化学习目标。"),
    "Attribution": ("Attribution", "归因", "按设定窗口和规则把转化归到广告互动。", None, "理解报告数字为何可能与其他系统不同。", "比较不同归因窗口下的报告。"),
    "Frequency": ("Frequency", "频次", "平均每人看到广告的次数。", "Impressions / Reach", "观察重复触达与素材疲劳风险。", "1000 次展示、500 人触达，平均频次为 2。"),
    "Learning Phase": ("Learning Phase", "学习阶段", "系统在收集结果并调整投放的阶段。", None, "避免把短期波动当作稳定表现。", "新广告组初期观察结果波动。"),
}

ALIASES = {name: (name.lower(),) for name in TOPICS}
ALIASES.update({
    "Campaign": ("campaign", "广告系列"), "Ad Set": ("ad set", "广告组"),
    "Ad": ("单条广告", "广告层级", "ad 是什么"),
    "Pixel": ("pixel", "像素"), "CAPI": ("capi", "conversions api"),
    "Conversion Event": ("conversion event", "转化事件"),
    "Audience": ("audience", "受众"),
    "Custom Audience": ("custom audience", "自定义受众"),
    "Lookalike Audience": ("lookalike audience", "类似受众"),
    "Placement": ("placement", "版位"),
    "Advantage+ Placements": ("advantage+ placements", "advantage+ 版位", "自动版位"),
    "Optimization": ("optimization", "优化"), "Attribution": ("attribution", "归因"),
    "Frequency": ("frequency", "频次"), "Learning Phase": ("learning phase", "学习阶段"),
})

METRICS = {"CPM", "CPC", "CTR", "CPA", "ROAS", "Frequency"}


def explain_meta_ads_concept(user_goal):
    """返回单个概念；未指定时列出可学主题。"""
    topic = find_topic(user_goal, ALIASES)
    if topic is None:
        return {"success": True, "platform": "meta_ads", "topic": "概念目录", "available_topics": list(TOPICS)}
    name, chinese, explanation, formula, why, example = TOPICS[topic]
    mistakes = (["混用点击、行动或归因口径", "只看指标，不检查最终业务结果"]
                if topic in METRICS else
                ["忽略所选广告目标及账户设置", "把某项功能当成所有目标都适用"])
    return {
        "success": True, "platform": "meta_ads", "topic": topic,
        "name": name, "chinese_name": chinese, "explanation": explanation,
        "formula": formula, "why_it_matters": why, "example": example,
        "common_mistakes": mistakes,
    }
