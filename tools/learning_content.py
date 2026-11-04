"""概念与案例工具共用的简单主题匹配函数。"""


def find_topic(goal, aliases):
    """优先匹配较长的别名，避免 Conversion Value 被识别成 Conversion。"""
    text = goal.lower()
    choices = [(alias.lower(), topic) for topic, words in aliases.items() for alias in words]
    for alias, topic in sorted(choices, key=lambda item: len(item[0]), reverse=True):
        if alias in text:
            return topic
    return None
