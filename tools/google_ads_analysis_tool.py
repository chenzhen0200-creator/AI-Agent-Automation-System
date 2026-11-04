"""Google Ads 案例分析：只提供排查思路，不读取账户。"""

from tools.learning_content import find_topic


# 可能原因、检查项、建议学习动作、优先级。
CASES = {
    "CTR 高但转化低": ("搜索意图与落地页不匹配；转化追踪可能漏记", "核对搜索词与落地页；检查表单和转化事件", "按搜索词分组复盘；用测试流程核验转化记录", "high"),
    "CPC 高": ("竞争加剧；广告或落地页相关性不足", "比较关键词和设备 CPC；查看搜索词与质量诊断", "整理不相关搜索词；学习改进广告与落地页相关性", "medium"),
    "CPM 高": ("曝光竞争变化；目标场景范围较窄", "比较地区、时段和素材；核对展示成本与转化", "分段复盘成本变化；检查素材适配", "medium"),
    "CPA 高": ("点击后的转化率下降；转化定义或成本变化", "拆分 CPC 与转化率；检查转化追踪", "先排除追踪异常；复盘落地页和流量质量", "high"),
    "ROAS 低": ("转化价值漏记；低价值流量占比上升", "核对收入和费用口径；按商品与广告系列拆分", "先核实价值回传；学习按价值分析结果", "high"),
    "Conversion 下降": ("追踪中断；流量或落地页表现变化", "检查转化事件状态；比较展示、点击和转化率", "先排除技术故障；按时间和设备定位变化", "high"),
    "花费不出去": ("广告未获批准；定向或出价目标过于限制", "检查审核与投放状态；查看受众、地区和预算限制", "先确认可投放状态；学习排查限制条件", "medium"),
    "展示量低": ("覆盖范围小；广告或商品状态异常", "查看展示份额与审核状态；检查关键词和商品覆盖", "按广告类型逐项排查覆盖范围", "medium"),
    "点击多但无转化": ("流量意图不匹配；落地页或转化记录异常", "查看搜索词与跳出路径；测试转化流程", "先验证记录；再学习优化关键词和页面", "high"),
    "搜索词不相关": ("关键词匹配范围过宽；否定关键词不足", "打开搜索词报告；对照实际查询与业务目标", "归类无关查询；学习匹配类型与否定关键词", "medium"),
    "PMax 表现差": ("转化目标或价值信号质量不足；素材组覆盖不全", "核对转化设置；查看素材组和商品状态", "先校验目标与数据；复盘素材和商品质量", "high"),
    "Video Campaign 观看多但转化少": ("视频吸引观看但行动号召弱；目标与衡量口径不匹配", "比较观看与网站行动；检查 CTA 和落地页", "学习区分观看目标与转化目标；复盘点击后路径", "medium"),
}

ALIASES = {
    "CTR 高但转化低": ("ctr高但转化低", "ctr 高但转化低", "点击率高但转化低"),
    "CPC 高": ("cpc", "每次点击费用高"),
    "CPM 高": ("cpm", "千次展示费用高"),
    "CPA 高": ("cpa", "每次转化费用高"),
    "ROAS 低": ("roas", "回报低"),
    "Conversion 下降": ("conversion下降", "转化下降", "conversion 下降"),
    "花费不出去": ("花费不出去", "预算花不出去", "消耗不足"),
    "展示量低": ("展示量低", "展示少", "impressions low"),
    "点击多但无转化": ("点击多但无转化", "点击多没转化", "有点击无转化"),
    "搜索词不相关": ("搜索词不相关", "搜索词无关"),
    "PMax 表现差": ("pmax表现差", "pmax 表现差", "performance max表现差"),
    "Video Campaign 观看多但转化少": ("观看多但转化少", "观看多没转化", "video campaign转化少"),
}


def analyze_google_ads_case(user_goal):
    """返回统一的案例分析字段。"""
    issue = find_topic(user_goal, ALIASES)
    if issue is None:
        return {"success": True, "platform": "google_ads", "topic": "案例目录", "available_issues": list(CASES)}
    causes, checks, actions, priority = CASES[issue]
    return {
        "success": True, "platform": "google_ads", "topic": issue, "issue": issue,
        "possible_causes": causes.split("；"), "checks": checks.split("；"),
        "recommended_actions": actions.split("；"), "priority": priority,
        "notes": "这是教学排查清单；未读取真实广告数据，需先核对指标口径。",
    }
