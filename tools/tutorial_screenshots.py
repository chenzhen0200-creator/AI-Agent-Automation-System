"""只从人工核实的真实后台截图清单中读取教学图片。"""

import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = PROJECT_ROOT / "data" / "tutorial_screenshots.json"
IMAGE_ROOT = PROJECT_ROOT / "frontend" / "tutorial-images"
SOURCES = {"user_upload", "google_official", "meta_official", "public_tutorial"}
IMAGE_PATH = re.compile(r"^(google|meta)/real/(?:[a-z0-9-]+/)+[a-z0-9-]+\.(?:png|jpg|jpeg|webp)$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _valid_image_file(path):
    try:
        with path.open("rb") as image:
            header = image.read(12)
    except OSError:
        return False
    suffix = path.suffix.lower()
    return ((suffix == ".png" and header.startswith(b"\x89PNG\r\n\x1a\n"))
            or (suffix in {".jpg", ".jpeg"} and header.startswith(b"\xff\xd8\xff"))
            or (suffix == ".webp" and header.startswith(b"RIFF") and header[8:12] == b"WEBP"))


def _valid_date(value):
    if not isinstance(value, str) or not DATE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _valid_source(source, source_url):
    if source == "user_upload":
        return source_url is None
    if not isinstance(source_url, str):
        return False
    try:
        parsed = urlparse(source_url)
        host = parsed.hostname
    except ValueError:
        return False
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        return False
    host = host.lower()
    if source == "google_official":
        return host in {"support.google.com", "ads.google.com", "developers.google.com"}
    if source == "meta_official":
        return host in {"facebook.com", "www.facebook.com", "developers.facebook.com", "business.facebook.com", "www.meta.com"}
    return source == "public_tutorial"


def screenshots_for(platform, topic, variant=None):
    """只有图片文件存在、路径安全、来源完整时才提供 URL。"""
    try:
        entries = json.loads(MANIFEST.read_text(encoding="utf-8")).get("screenshots", [])
    except (OSError, ValueError, AttributeError):
        return {}
    if not isinstance(entries, list):
        return {}
    folder = {"google_ads": "google", "meta_ads": "meta"}.get(platform)
    if not folder:
        return {}
    found = {}
    for item in entries:
        if not isinstance(item, dict) or item.get("platform") != platform or item.get("topic") != topic or item.get("variant") != variant:
            continue
        path = item.get("path")
        number = item.get("step_number")
        source = item.get("image_source")
        captured = item.get("captured_at")
        if (not isinstance(path, str) or not IMAGE_PATH.fullmatch(path) or not path.startswith(folder + "/real/")
                or not isinstance(number, int) or isinstance(number, bool) or number < 1
                or not isinstance(source, str) or source not in SOURCES or not _valid_date(captured)
                or item.get("rights_cleared") is not True
                or item.get("cropped_to_step") is not True
                or (source == "user_upload" and (item.get("redacted") is not True or item.get("publish_approved") is not True))
                or not _valid_source(source, item.get("source_url"))):
            continue
        image_file = IMAGE_ROOT / path
        if not image_file.is_file() or not _valid_image_file(image_file):
            continue
        found[number] = {
            "image_url": "/static/tutorial-images/" + path,
            "image_type": "real_screenshot",
            "image_source": source,
            "source_url": item.get("source_url"),
            "captured_at": captured,
        }
    return found
