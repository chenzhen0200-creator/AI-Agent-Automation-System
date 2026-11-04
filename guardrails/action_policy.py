"""显式维护可执行的只读学习工具和禁止的账户动作。"""

ALLOWED_ACTIONS = frozenset({
    "explain_google_ads_concept", "explain_meta_ads_concept",
    "get_google_ads_steps", "get_meta_ads_steps",
    "analyze_google_ads_case", "analyze_meta_ads_case",
    "compare_google_meta", "get_learning_progress",
    "search_learning_memory", "search_ads_knowledge", "analyze_ads_screenshot",
})

BLOCKED_ACTIONS = frozenset({
    "create_campaign", "create_ad", "update_campaign", "update_campaign_budget",
    "modify_budget", "update_bid", "delete_campaign", "delete_ad",
    "recharge_account", "make_payment", "change_account_permissions", "submit_ad",
})

MEDIUM_RISK_ACTIONS = frozenset({
    "analyze_ads_screenshot", "analyze_google_ads_case", "analyze_meta_ads_case",
    "get_google_ads_steps", "get_meta_ads_steps",
})
