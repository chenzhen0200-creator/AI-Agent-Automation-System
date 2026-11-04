"""抓取所选网页的标题与相关段落，不保存整页。"""

from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from retrieval.source_filter import classify_source
from errors import make_error


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None  # 重新定向可能跳到未审核的域名。


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tag = None
        self.skip = 0
        self.parts = []
        self.title = ""
        self.updated_at = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in ("script", "style", "nav", "footer"):
            self.skip += 1
        if tag == "meta" and values.get("content"):
            key = values.get("property", values.get("name", "")).lower()
            if key in ("article:modified_time", "date.modified", "last-modified"):
                self.updated_at = self.updated_at or values["content"]
        if tag in ("title", "h1", "h2", "h3", "p", "li"):
            self.tag = tag

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer") and self.skip:
            self.skip -= 1
        if tag == self.tag:
            self.tag = None

    def handle_data(self, data):
        if self.skip or not self.tag:
            return
        clean = " ".join(data.split())
        if not clean:
            return
        if self.tag == "title":
            self.title += clean + " "
        elif len(clean) >= 30:
            self.parts.append(clean)


def extract_content(source, query, platform):
    """只处理已过滤的 HTTPS 来源，并限制响应与输出长度。"""
    url = source.get("url", "")
    try:
        approved = urlparse(url).scheme == "https" and classify_source(source, platform) == source.get("source_type")
    except (TypeError, ValueError):
        approved = False
    if not approved:
        return make_error("Source Rejected", "网页来源未通过安全筛选")
    request = Request(url, headers={"User-Agent": "AdsLearningAgent/1.0", "Accept": "text/html"})
    try:
        with build_opener(_NoRedirect).open(request, timeout=10) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                raise ValueError("非 HTML 页面")
            body = response.read(250001)
            if len(body) > 250000:
                raise ValueError("页面过大")
            charset = response.headers.get_content_charset() or "utf-8"
            html = body.decode(charset, errors="replace")
    except (HTTPError, URLError, TimeoutError, ValueError, LookupError):
        return make_error("Content Extraction Failed", "无法提取网页正文")
    parser = _PageParser()
    try:
        parser.feed(html)
    except ValueError:
        return make_error("Content Extraction Failed", "网页正文解析失败")
    words = [word.lower() for word in query.split() if len(word) > 1]
    relevant = [part for part in parser.parts if any(word in part.lower() for word in words)]
    # 相关段落不足时使用靠前的正文，仍限制长度并保留来源。
    selected = (relevant or parser.parts[:5])[:8]
    content = "\n".join(selected)[:3000]
    if not content:
        return make_error("Content Extraction Failed", "网页没有可提取的正文")
    return {"success": True, "title": parser.title.strip() or source.get("title", ""), "url": url,
            "updated_at": parser.updated_at, "relevant_sections": selected,
            "content": content}
