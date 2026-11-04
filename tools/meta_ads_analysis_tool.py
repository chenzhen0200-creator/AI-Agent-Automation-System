"""Meta Ads 案例分析：只提供排查思路，不读取账户。"""

from tools.learning_content import find_topic


CASES = {
    "CPM 高": ("受众竞争变化；版位或地区覆盖受限", "比较受众与版位 CPM；检查季节和素材", "先分段确认变化来源；复盘素材适配", "medium"),
    "CTR 低": ("素材与人群不匹配；广告开头吸引力不足", "按版位看点击口径；比较素材和受众", "学习测试不同创意角度；核对链接预览", "medium"),
    "CPC 高": ("CPM 上升；CTR 下降", "分别检查 CPM 和 CTR；确认点击指标口径", "先定位曝光成本或素材问题", "medium"),
    "CPA 高": ("转化率下降；事件口径变化", "核对 Pixel/CAPI 事件；检查点击后页面", "先确认追踪；再分析素材和落地页", "high"),
    "ROAS 低": ("购买价值漏记；高费用低价值订单增多", "核对 Purchase 价值；检查归因和退款口径", "先验证收入回传；按素材和受众分段", "high"),
    "Frequency 高": ("重复触达增加；受众范围较窄", "比较频次、CTR 与 CPA 的时间趋势；检查触达人数", "学习素材轮换；复盘受众覆盖范围", "medium"),
    "素材疲劳": ("重复展示使素材吸引力下降；创意角度单一", "观察频次和 CTR 趋势；比较新旧素材", "准备不同创意角度；学习受众与版位适配", "medium"),
    "受众过窄": ("地区、兴趣和排除条件交集太小；来源受众规模不足", "核对受众规模；检查排除条件", "学习扩大测试范围；比较不同受众假设", "medium"),
    "Pixel 没有回传": ("Pixel 未触发；事件参数或网站实现异常", "使用事件测试查看触发；检查事件名称与浏览器请求", "先复核安装与触发路径；再学习事件去重", "high"),
    "CAPI 异常": ("服务器事件未送达；参数或去重信息缺失", "查看事件诊断；核对 event_id 与事件时间", "先定位传输或参数问题；学习浏览器与服务器事件去重", "high"),
    "AddToCart 多但 Purchase 少": ("结账流程阻塞；加购人群意图较弱", "比较加购到购买转化率；检查支付和运费环节", "先排除站点故障；复盘结账漏斗", "high"),
    "Learning Limited": ("可用于优化的事件不足；广告组设置过于分散", "查看优化事件量；检查受众及广告组拆分", "学习减少不必要的结构碎片；核对事件质量", "medium"),
    "广告花费突然下降": ("广告审核或投放状态变化；受众、出价或事件信号变化", "检查投放诊断；比较预算、频次和事件状态", "先排除状态与追踪故障；再定位设置变化", "high"),
    "转化下降": ("事件记录异常；点击质量或页面转化率变化", "核对 Pixel/CAPI；比较流量、页面和归因窗口", "先确认事件正常；按时间和素材拆分", "high"),
}

ALIASES = {
    "CPM 高": ("cpm", "千次展示费用高"), "CTR 低": ("ctr", "点击率低"),
    "CPC 高": ("cpc", "每次点击费用高"), "CPA 高": ("cpa", "每次行动费用高"),
    "ROAS 低": ("roas", "回报低"), "Frequency 高": ("frequency", "频次高"),
    "素材疲劳": ("素材疲劳", "创意疲劳"),
    "受众过窄": ("受众过窄", "受众太窄", "人群过窄"),
    "Pixel 没有回传": ("pixel没有回传", "pixel 没有回传", "pixel不回传", "像素没回传"),
    "CAPI 异常": ("capi异常", "capi 异常", "conversions api异常"),
    "AddToCart 多但 Purchase 少": ("addtocart", "加购多但购买少", "purchase少"),
    "Learning Limited": ("learning limited", "学习受限"),
    "广告花费突然下降": ("花费突然下降", "消耗突然下降", "广告花费下降"),
    "转化下降": ("转化下降", "购买下降"),
}


def analyze_meta_ads_case(user_goal):
    """返回统一的案例分析字段。"""
    issue = find_topic(user_goal, ALIASES)
    if issue is None:
        return {"success": True, "platform": "meta_ads", "topic": "案例目录", "available_issues": list(CASES)}
    causes, checks, actions, priority = CASES[issue]
    return {
        "success": True, "platform": "meta_ads", "topic": issue, "issue": issue,
        "possible_causes": causes.split("；"), "checks": checks.split("；"),
        "recommended_actions": actions.split("；"), "priority": priority,
        "notes": "这是教学排查清单；未读取真实广告数据，需先核对事件与归因口径。",
    }
