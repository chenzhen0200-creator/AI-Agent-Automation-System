"""Google Ads 与 Meta Ads 的八类结构化学习对比。"""

from tools.learning_content import find_topic


# Google 机制、优势、限制；Meta 机制、优势、限制；关键区别、适用场景。
TOPICS = {
    "Google Search vs Meta Feed Ads": (
        "按搜索查询及相关关键词触达主动寻找信息的人。", ["搜索意图较明确"], ["依赖可覆盖的搜索需求"],
        "在 Feed 等浏览场景中用受众信号和素材触达用户。", ["适合展示视觉创意"], ["用户未必正在主动搜索"],
        "搜索意图与浏览发现的触发方式不同。", "已有明确搜索需求时学习 Search；希望展示创意并发现潜在人群时学习 Feed。"),
    "Google Video vs Meta Video Ads": (
        "在 YouTube 等视频场景用视频广告触达用户。", ["适合较长的视频叙事"], ["观看不一定带来转化"],
        "在 Feed、Stories、Reels 等版位展示视频创意。", ["便于适配社交浏览场景"], ["不同版位需要适配素材"],
        "视频消费场景和版位结构不同。", "根据目标受众的视频使用场景、素材比例和衡量目标选择。"),
    "Google PMax vs Meta Advantage+": (
        "跨 Google 多个渠道围绕转化目标自动优化。", ["整合多渠道覆盖"], ["部分细分控制有限"],
        "Meta 的 Advantage+ 自动化功能根据具体产品配置进行分发或优化。", ["减少部分手动配置"], ["可用选项随产品变化"],
        "覆盖的渠道和可控项不同，名称相近不代表机制相同。", "先比较业务目标、素材和事件数据，再分别学习两种自动化方案。"),
    "Google Conversion Tracking vs Meta Pixel/CAPI": (
        "用转化动作、网站标记或导入数据衡量目标行动。", ["可与出价目标关联"], ["需要正确配置转化动作与价值"],
        "用 Pixel 浏览器事件和 CAPI 服务器事件记录行为。", ["可结合浏览器与服务器信号"], ["需要关注事件去重和质量"],
        "事件来源与去重机制不同，报告数字不可直接视为同口径。", "先统一事件定义、价值和归因窗口，再比较平台报告。"),
    "Google Keywords vs Meta Audience": (
        "Search 关键词提供与用户查询相关的匹配线索。", ["贴近主动搜索意图"], ["受搜索量和匹配范围约束"],
        "受众定义或信号帮助系统找到可能感兴趣的人。", ["适合探索潜在人群"], ["意图可能不如搜索查询明确"],
        "一个从查询词出发，一个更侧重人群信号与素材互动。", "明确需求可先研究关键词；需求培育可先研究受众和创意。"),
    "Google Bidding vs Meta Optimization": (
        "根据点击、转化或转化价值等目标设置出价策略。", ["目标类型清晰"], ["目标依赖可靠的转化数据"],
        "选择优化事件和投放目标，让系统争取相应结果。", ["优化与事件结合紧密"], ["事件量或质量不足会影响学习"],
        "两平台优化对象和可用控制项不同。", "先确定业务结果与可用事件，再分别研究平台可用策略。"),
    "Google Attribution vs Meta Attribution": (
        "按 Google Ads 的转化设置和归因模型分配转化贡献。", ["可分析广告路径贡献"], ["与其他系统口径可能不同"],
        "按 Meta 的归因设置与事件数据报告转化。", ["可连接广告互动与事件"], ["窗口和去重口径影响报告"],
        "归因窗口、事件来源和报告规则可能不同。", "对比前统一时间、事件、价值和归因窗口。"),
    "Google Campaign Structure vs Meta Campaign Structure": (
        "通常按 Campaign、Ad Group、Ad 组织，部分类型使用资产组。", ["层级便于组织搜索主题"], ["不同广告类型结构不完全相同"],
        "通常按 Campaign、Ad Set、Ad 组织。", ["层级分离目标、投放条件和素材"], ["过度拆分可能增加学习复杂度"],
        "Google Ad Group 与 Meta Ad Set 的职责并不完全相同。", "先画出目标、定向和素材所在层级，再学习各自界面。"),
}

ALIASES = {
    "Google Search vs Meta Feed Ads": ("search", "feed", "信息流", "搜索广告"),
    "Google Video vs Meta Video Ads": ("video", "youtube", "视频"),
    "Google PMax vs Meta Advantage+": ("pmax", "performance max", "advantage+"),
    "Google Conversion Tracking vs Meta Pixel/CAPI": ("conversion tracking", "pixel", "capi", "转化追踪"),
    "Google Keywords vs Meta Audience": ("keywords", "keyword", "关键词", "受众"),
    "Google Bidding vs Meta Optimization": ("bidding", "optimization", "出价", "优化"),
    "Google Attribution vs Meta Attribution": ("attribution", "归因"),
    "Google Campaign Structure vs Meta Campaign Structure": ("campaign structure", "campaign", "结构", "广告系列"),
}


def compare_google_meta(user_goal):
    """返回一个比较主题，未指定时提供目录。"""
    topic = find_topic(user_goal, ALIASES)
    if topic is None:
        return {"success": True, "topic": "对比目录", "available_topics": list(TOPICS)}
    google_how, google_strengths, google_limits, meta_how, meta_strengths, meta_limits, difference, usage = TOPICS[topic]
    return {
        "success": True, "topic": topic,
        "google_ads": {"how_it_works": google_how, "strengths": google_strengths, "limitations": google_limits},
        "meta_ads": {"how_it_works": meta_how, "strengths": meta_strengths, "limitations": meta_limits},
        "key_difference": difference, "when_to_use_each": usage,
    }
