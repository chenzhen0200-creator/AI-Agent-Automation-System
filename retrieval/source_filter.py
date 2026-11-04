"""只允许可判断来源的官方站点或明确列入清单的第三方。"""

from urllib.parse import urlparse


OFFICIAL_DOMAINS = {
    "google_ads": ("support.google.com", "ads.google.com", "developers.google.com", "blog.google"),
    "meta_ads": ("facebook.com", "www.facebook.com", "developers.facebook.com", "about.fb.com"),
}
TRUSTED_THIRD_PARTY = ("searchengineland.com",)


def _official(platform, host, path):
    if platform == "google_ads":
        return ((host == "support.google.com" and path.startswith("/google-ads"))
                or host == "ads.google.com"
                or (host == "developers.google.com" and path.startswith("/google-ads"))
                or (host == "blog.google" and path.startswith("/products/ads")))
    return ((host in ("facebook.com", "www.facebook.com") and path.startswith("/business"))
            or host == "developers.facebook.com" or host == "about.fb.com")


def classify_source(result, platform):
    """未知、广告农场和无来源页面不进入结果。"""
    try:
        parsed = urlparse(result.get("url", ""))
    except (TypeError, ValueError):
        return None
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    host = parsed.hostname.lower()
    platforms = ("google_ads", "meta_ads") if platform == "cross_platform" else (platform,)
    if any(_official(name, host, parsed.path) for name in platforms):
        return "official"
    if host in TRUSTED_THIRD_PARTY or any(host.endswith("." + domain) for domain in TRUSTED_THIRD_PARTY):
        text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
        if any(word in text for word in ("google ads", "meta ads", "facebook ads", "广告")):
            return "third_party"
    return None


def filter_sources(results, platform, official_only=True):
    """附加 source_type，并按官方优先策略过滤。"""
    selected = []
    for result in results:
        source_type = classify_source(result, platform)
        if source_type and (source_type == "official" or not official_only):
            selected.append({**result, "source_type": source_type})
    return selected
