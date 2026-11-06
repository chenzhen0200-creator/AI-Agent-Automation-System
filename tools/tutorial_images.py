"""把现有步骤数据绘制成不含账户信息的静态 SVG 教学界面示意。"""

from html import escape
from pathlib import Path

from tools.visual_steps import make_step, topic_slug


def _short(value, length=32):
    text = str(value).replace("\n", " ")
    return escape(text[:length] + ("…" if len(text) > length else ""))


def _svg(platform, topic, step):
    accent = "#2563eb" if platform == "google" else "#087f79"
    pale = "#eff6ff" if platform == "google" else "#eaf8f5"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 510" role="img" aria-label="{_short(topic)} 第 {step['step_number']} 步界面示意">
<rect width="900" height="510" fill="#f3f6fa"/><rect x="28" y="24" width="844" height="460" rx="18" fill="white" stroke="#dbe3eb"/>
<rect x="28" y="24" width="844" height="60" rx="18" fill="{pale}"/><text x="55" y="62" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#263a55">AdLearn · {escape(platform.title())} Ads 教学</text>
<text x="840" y="61" text-anchor="end" font-family="Arial, sans-serif" font-size="15" fill="{accent}">界面示意 · 非官方截图</text>
<rect x="48" y="105" width="185" height="354" rx="10" fill="#f8fafc" stroke="#e3eaf0"/>
<text x="68" y="140" font-family="Arial, sans-serif" font-size="14" fill="#68788c">导航区域</text>
<rect x="66" y="164" width="145" height="12" rx="6" fill="#dce4ec"/><rect x="66" y="196" width="118" height="12" rx="6" fill="#dce4ec"/><rect x="66" y="228" width="138" height="12" rx="6" fill="#dce4ec"/>
<rect x="257" y="105" width="591" height="354" rx="10" fill="#ffffff" stroke="#e3eaf0"/>
<text x="285" y="142" font-family="Arial, sans-serif" font-size="17" font-weight="bold" fill="#263a55">{_short(topic)} · 第 {step['step_number']} 步</text>
<text x="285" y="180" font-family="Arial, sans-serif" font-size="16" fill="#5d6d80">{_short(step['title'], 42)}</text>
<text x="285" y="224" font-family="Arial, sans-serif" font-size="14" fill="#78899b">通常位于</text>
<text x="285" y="250" font-family="Arial, sans-serif" font-size="18" fill="#263a55">{_short(step['ui_location'], 38)}</text>
<rect x="285" y="280" width="530" height="90" rx="12" fill="{pale}" stroke="{accent}" stroke-width="2"/>
<circle cx="313" cy="325" r="12" fill="{accent}"/><text x="313" y="330" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="white">→</text>
<text x="337" y="330" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="{accent}">{_short(step['action'], 34)}</text>
<text x="285" y="411" font-family="Arial, sans-serif" font-size="14" fill="#617186">预期：{_short(step['expected_result'], 42)}</text>
</svg>'''


def build_tutorial_images(frontend_dir):
    """服务启动时生成静态图片，内容只来自项目内的教学步骤。"""
    from tools.google_ads_steps_tool import TOPIC_STEPS as google_topics
    from tools.meta_ads_steps_tool import TOPIC_STEPS as meta_topics, get_meta_ads_steps

    root = Path(frontend_dir) / "tutorial-images"
    for platform, topics in (("google", google_topics), ("meta", meta_topics)):
        for topic, items in topics.items():
            folder = root / platform / topic_slug(topic)
            folder.mkdir(parents=True, exist_ok=True)
            for number, item in enumerate(items, 1):
                step = make_step(number, *item)
                (folder / f"step-{number}.svg").write_text(_svg(platform, topic, step), encoding="utf-8")
    duplicate = get_meta_ads_steps("Meta Ads 复制 Ad Set")
    folder = root / "meta" / "ad-set-duplicate"
    folder.mkdir(parents=True, exist_ok=True)
    for step in duplicate["steps"]:
        (folder / f"step-{step['step_number']}.svg").write_text(_svg("meta", "Ad Set 复制", step), encoding="utf-8")
