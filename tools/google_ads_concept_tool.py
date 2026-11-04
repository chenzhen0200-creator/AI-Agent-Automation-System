"""Google Ads 概念解释：每个主题返回统一的教学字段。"""

from tools.learning_content import find_topic


# 英文名、中文名、解释、公式、学习价值、示例。
TOPICS = {
    "CPM": ("Cost per Mille", "千次展示费用", "每获得一千次广告展示的平均费用。", "Cost / Impressions × 1000", "观察曝光成本。", "花费 20 元获得 2000 次展示，CPM 为 10 元。"),
    "CPC": ("Cost per Click", "每次点击费用", "广告费用除以点击次数。", "Cost / Clicks", "观察获取访问的成本。", "花费 100 元获得 50 次点击，CPC 为 2 元。"),
    "CTR": ("Click-Through Rate", "点击率", "点击次数占展示次数的比例。", "Clicks / Impressions × 100%", "评估广告与受众或搜索意图的相关性。", "100 次展示、5 次点击，CTR 为 5%。"),
    "CPA": ("Cost per Action", "每次转化费用", "广告费用除以被统计的转化次数。", "Cost / Conversions", "衡量获得目标行动的成本。", "花费 200 元获得 10 次转化，CPA 为 20 元。"),
    "ROAS": ("Return on Ad Spend", "广告支出回报", "广告归因的转化价值与广告费用之比。", "Conversion Value / Cost", "比较投入与记录到的收入价值。", "花费 100 元、记录价值 400 元，ROAS 为 4 或 400%。"),
    "Conversion": ("Conversion", "转化", "用户完成了被定义为有价值的行动，例如购买或留资。", None, "决定优化和成效报告的目标。", "用户提交表单被记录为一次转化。"),
    "Conversion Value": ("Conversion Value", "转化价值", "为一次转化分配的金额或业务价值。", None, "支持按价值衡量和优化广告。", "一笔 300 元订单可记录 300 元价值。"),
    "Keywords": ("Keywords", "关键词", "用于匹配相关搜索需求的词或短语。", None, "帮助组织搜索广告的意图主题。", "给跑鞋广告组添加“跑鞋”相关关键词。"),
    "Search Terms": ("Search Terms", "搜索词", "用户实际使用的查询，与投放关键词可能不同。", None, "可检查流量是否相关。", "关键词是“跑鞋”，实际搜索词可能是“适合雨天的跑鞋”。"),
    "Match Type": ("Match Type", "关键词匹配类型", "决定关键词与搜索词的匹配范围。", None, "影响覆盖面和相关性。", "广泛匹配与完全匹配可能覆盖不同查询。"),
    "Quality Score": ("Quality Score", "质量得分", "搜索关键词的诊断指标，涉及预期 CTR、广告相关性和落地页体验。", None, "帮助定位搜索广告相关性问题。", "检查关键词的落地页体验分项。"),
    "Impression Share": ("Impression Share", "展示份额", "实际获得的展示次数占可获得展示机会的比例。", "Impressions / Eligible Impressions × 100%", "了解覆盖机会。", "获得 60 次展示、估计可获得 100 次，份额约 60%。"),
    "Search": ("Search Campaign", "搜索广告", "在相关搜索场景中展示的广告系列类型。", None, "适合学习主动搜索意图。", "用户搜索产品词时看到相关广告。"),
    "Video": ("Video Campaign", "视频广告", "以视频素材为核心的广告系列类型，可覆盖 YouTube 等场景。", None, "用于学习视频触达与观看指标。", "为新品准备介绍视频并选择视频广告目标。"),
    "Performance Max": ("Performance Max", "效果最大化广告", "跨 Google 多个渠道围绕转化目标进行优化的广告系列。", None, "理解素材组、受众信号和转化价值。", "准备文字、图片和视频素材组成资产组。"),
    "Demand Gen": ("Demand Gen", "需求开发广告", "面向视觉内容场景的广告系列类型。", None, "学习素材与受众在需求培育中的作用。", "用图片和视频介绍新产品。"),
    "Display": ("Display Campaign", "展示广告", "在展示网络相关版位呈现的广告系列。", None, "学习视觉素材与受众覆盖。", "用横幅素材向潜在客户展示产品。"),
    "Shopping": ("Shopping Campaign", "购物广告", "依赖商品数据源展示商品信息的广告系列。", None, "学习商品数据质量与销售衡量。", "用商品标题、价格和图片展示商品。"),
    "Bidding": ("Bidding", "出价", "根据目标决定广告竞价方式的设置。", None, "影响流量、转化和费用分配。", "以点击或转化作为优化方向。"),
    "Maximize Clicks": ("Maximize Clicks", "尽可能争取点击", "自动出价以在预算内争取尽可能多的点击。", None, "适合理解以流量为目标的策略。", "以网站访问量为学习目标时研究该策略。"),
    "Maximize Conversions": ("Maximize Conversions", "尽可能提高转化次数", "自动出价以在预算内争取更多转化。", None, "学习以转化量为目标的优化。", "已正确记录提交表单事件后研究该策略。"),
    "Target CPA": ("Target CPA", "目标每次转化费用", "以目标平均每次转化费用争取转化。", None, "理解成本目标与转化量之间的取舍。", "把期望 CPA 与实际 CPA 对照学习。"),
    "Target ROAS": ("Target ROAS", "目标广告支出回报", "以目标回报水平争取转化价值。", None, "学习价值导向的出价。", "先确认订单价值回传，再研究目标 ROAS。"),
}

ALIASES = {name: (name.lower(),) for name in TOPICS}
ALIASES.update({
    "Conversion Value": ("conversion value", "转化价值"),
    "Conversion": ("conversion", "转化"),
    "Keywords": ("keywords", "keyword", "关键词"),
    "Search Terms": ("search terms", "搜索词"),
    "Match Type": ("match type", "匹配类型"),
    "Quality Score": ("quality score", "质量得分"),
    "Impression Share": ("impression share", "展示份额"),
    "Search": ("search", "搜索广告"),
    "Video": ("youtube", "video", "视频广告"),
    "Performance Max": ("performance max", "pmax"),
    "Demand Gen": ("demand gen",),
    "Display": ("display", "展示广告"),
    "Shopping": ("shopping", "购物广告"),
    "Bidding": ("bidding", "出价"),
    "Maximize Clicks": ("maximize clicks", "尽可能争取点击"),
    "Maximize Conversions": ("maximize conversions", "尽可能提高转化"),
    "Target CPA": ("target cpa", "目标 cpa"),
    "Target ROAS": ("target roas", "目标 roas"),
})

METRICS = {"CPM", "CPC", "CTR", "CPA", "ROAS", "Impression Share"}


def explain_google_ads_concept(user_goal):
    """返回单个概念；未指定时提供可学主题目录。"""
    topic = find_topic(user_goal, ALIASES)
    if topic is None:
        return {"success": True, "platform": "google_ads", "topic": "概念目录", "available_topics": list(TOPICS)}
    name, chinese, explanation, formula, why, example = TOPICS[topic]
    mistakes = (["把不同时间段或统计口径的数字直接比较", "只看单一指标，不检查转化质量"]
                if topic in METRICS else
                ["忽略广告目标或设置条件", "把某个概念当成所有广告类型都适用"])
    return {
        "success": True, "platform": "google_ads", "topic": topic,
        "name": name, "chinese_name": chinese, "explanation": explanation,
        "formula": formula, "why_it_matters": why, "example": example,
        "common_mistakes": mistakes,
    }
