"""可选的 Brave Web Search 客户端；没有密钥时不发请求。"""

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from config import SEARCH_API_KEY_ENV_NAME
from errors import make_error
from recovery.retry_policy import run_with_retry


SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


def search_web(query, platform, domain_filter=None, freshness_required=False):
    """返回标准化搜索结果；domain_filter 使用 Brave 的 site: 操作符。"""
    api_key = os.getenv(SEARCH_API_KEY_ENV_NAME, "")
    if not api_key:
        return make_error("Search API Not Configured", "未配置真实搜索 API，无法执行外部检索")
    if not isinstance(query, str) or not query.strip() or platform not in ("google_ads", "meta_ads", "cross_platform"):
        return make_error("Validation Error", "搜索问题或平台无效")
    if domain_filter and (not isinstance(domain_filter, str) or not re.fullmatch(r"[a-zA-Z0-9.-]+", domain_filter)):
        return make_error("Validation Error", "域名筛选条件无效")
    search_query = f"{query} site:{domain_filter}" if domain_filter else query
    parameters = {"q": search_query, "count": 20, "safesearch": "strict"}
    if freshness_required:
        parameters["freshness"] = "py"
    request = Request(f"{SEARCH_URL}?{urlencode(parameters)}", headers={"X-Subscription-Token": api_key, "Accept": "application/json"})
    def request_once():
        try:
            with urlopen(request, timeout=15) as response:
                return {"success": True, "payload": json.loads(response.read().decode("utf-8"))}
        except HTTPError as error:
            return make_error("Search Request Failed", f"外部搜索失败（HTTP {error.code}）",
                              retryable=error.code == 429 or 500 <= error.code < 600)
        except (URLError, TimeoutError):
            return make_error("Search Request Failed", "外部搜索网络请求失败", retryable=True)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return make_error("Search Request Failed", "外部搜索响应解析失败")

    response, retry_count = run_with_retry(request_once, "search_ads_knowledge")
    if not response["success"]:
        response["retry_count"] = retry_count
        return response
    payload = response["payload"]
    web = payload.get("web") if isinstance(payload, dict) else None
    rows = web.get("results", []) if isinstance(web, dict) else []
    if not isinstance(rows, list):
        return make_error("Search Request Failed", "搜索响应格式不正确", retry_count=retry_count)
    results = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("url"), str) or not row["url"].startswith("https://"):
            continue
        url = row["url"]
        page_age = row.get("page_age")
        published_at = page_age if isinstance(page_age, str) and re.match(r"^\d{4}-\d{2}-\d{2}", page_age) else None
        results.append({"title": row.get("title", ""), "url": url, "snippet": row.get("description", ""),
                        "domain": urlparse(url).hostname or "", "published_at": published_at})
    return {"success": True, "results": results, "retry_count": retry_count}
