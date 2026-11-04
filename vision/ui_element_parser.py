"""把视觉观察统一为可供教学使用的 UI 元素。"""

ELEMENT_TYPES = {"button", "tab", "menu", "field", "warning", "label"}
STATES = {"visible", "selected", "disabled", "unknown"}
LEGACY_FIELDS = {
    "visible_buttons": "button", "visible_navigation": "menu",
    "visible_fields": "field", "selected_items": "label",
    "warning_messages": "warning",
}


def _normalize(item, default_type=None):
    if isinstance(item, str):
        item = {"text": item}
    if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not item["text"].strip():
        return None
    element_type = item.get("element_type", default_type)
    if not isinstance(element_type, str) or element_type not in ELEMENT_TYPES:
        return None
    confidence = item.get("confidence", 0.0)
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        confidence = 0.0
    state = item.get("state", "unknown")
    return {
        "element_type": element_type,
        "text": item["text"].strip()[:120],
        "location": item.get("location", "")[:120] if isinstance(item.get("location", ""), str) else "",
        "state": state if isinstance(state, str) and state in STATES else "unknown",
        "confidence": float(confidence),
    }


def parse_ui_elements(observation):
    """忽略格式错误的控件，不推断截图中未报告的元素。"""
    elements = []
    raw = observation.get("elements", [])
    if isinstance(raw, list):
        for item in raw:
            element = _normalize(item)
            if element:
                elements.append(element)
    for field, element_type in LEGACY_FIELDS.items():
        values = observation.get(field, [])
        if isinstance(values, list):
            for item in values:
                element = _normalize(item, element_type)
                if element:
                    if field == "selected_items" and element["state"] == "unknown":
                        element["state"] = "selected"
                    elements.append(element)
    unique = {}
    for element in elements:
        key = (element["element_type"], element["text"].casefold(), element["location"].casefold())
        if key not in unique or unique[key]["confidence"] < element["confidence"]:
            unique[key] = element
    return list(unique.values())[:80]
