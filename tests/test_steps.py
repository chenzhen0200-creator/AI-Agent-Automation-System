"""检查教学步骤的覆盖范围与回答完整性。运行：python -m unittest discover -s tests"""

import unittest
import json
import base64
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from agents.answer_composer import _render
from agents.ads_learning_agent import run_ads_learning_agent
from tools.google_ads_steps_tool import get_google_ads_steps
from tools.meta_ads_steps_tool import get_meta_ads_steps
from tools.google_ads_steps_tool import TOPIC_STEPS as GOOGLE_TOPICS
from tools.meta_ads_steps_tool import TOPIC_STEPS as META_TOPICS
from tools.visual_steps import attach_images
from tools.tutorial_screenshots import screenshots_for


class StepTeachingTests(unittest.TestCase):
    def test_every_registered_topic_has_enough_steps(self):
        for platform, topics in (("Google Ads", GOOGLE_TOPICS), ("Meta Ads", META_TOPICS)):
            for topic, steps in topics.items():
                with self.subTest(platform=platform, topic=topic):
                    self.assertGreaterEqual(len(steps), 6 if topic == "Campaign" or topic in (
                        "Search", "Video / YouTube", "Performance Max", "Demand Gen", "Display", "Shopping"
                    ) else 5)

    def check_topic(self, tool, question, expected_topic, minimum):
        result = tool(question)
        self.assertTrue(result["success"])
        self.assertEqual(result["topic"], expected_topic)
        steps = result["steps"]
        self.assertGreaterEqual(len(steps), minimum)
        self.assertEqual([item["step_number"] for item in steps], list(range(1, len(steps) + 1)))
        for item in steps:
            for field in ("title", "ui_location", "action", "description", "expected_result", "image_hint", "platform"):
                self.assertTrue(item.get(field), f"{expected_topic}: {field} 不应为空")
            if item["image_url"]:
                self.assertEqual(item["image_type"], "real_screenshot")
                self.assertTrue(item["image_source"])
            else:
                self.assertIsNone(item["image_type"])
        return result

    def test_meta_topics(self):
        for question, topic in (
            ("Meta Ads Campaign 怎么创建", "Campaign"),
            ("Meta Ads 广告组在哪里设置", "Ad Set"),
            ("Meta Ads Audience 怎么设置", "Audience"),
            ("Meta Ads Placement 怎么设置", "Placement"),
            ("Meta Ads Pixel 怎么设置", "Pixel"),
            ("Meta Ads CAPI 怎么设置", "CAPI"),
        ):
            with self.subTest(topic=topic):
                self.check_topic(get_meta_ads_steps, question, topic, 6 if topic == "Campaign" else 5)

    def test_google_topics(self):
        for question, topic in (
            ("Google Ads Campaign 怎么创建", "Campaign"),
            ("Google Ads 怎么进入 Ad Group", "Ad Group"),
            ("Google Ads 关键词在哪里添加", "Keywords"),
            ("Google Ads Audience 怎么设置", "Audiences"),
            ("Google Ads Bidding 怎么设置", "Bidding"),
            ("Google Ads 怎么创建搜索广告", "Search"),
            ("Google Ads Video / YouTube 怎么创建", "Video / YouTube"),
        ):
            with self.subTest(topic=topic):
                self.check_topic(get_google_ads_steps, question, topic, 6 if topic in ("Campaign", "Search", "Video / YouTube") else 5)

    def test_answer_is_brief_but_keeps_every_step(self):
        result = self.check_topic(get_meta_ads_steps, "Meta Ads 广告组在哪里设置", "Ad Set", 5)
        answer = _render("get_meta_ads_steps", result)
        self.assertIn(f"第 {len(result['steps'])} 步：", answer)
        self.assertEqual(answer.count("第 "), len(result["steps"]))
        for label in ("位置：", "说明：", "预期结果：", "图示提示："):
            self.assertNotIn(label, answer)
        self.assertTrue(all(step["image_url"] is None or "/real/" in step["image_url"] for step in result["steps"]))

    def test_old_mock_url_is_removed(self):
        old_step = {"step_number": 5, "image_url": "/static/tutorial-images/meta/ad-set-duplicate/step-5.svg"}
        cleaned = attach_images([old_step], "meta_ads", "Ad Set", "Ad Set Duplicate")
        self.assertNotEqual(cleaned[0]["image_url"], "/static/tutorial-images/meta/ad-set-duplicate/step-5.svg")
        if cleaned[0]["image_url"]:
            self.assertEqual(cleaned[0]["image_type"], "real_screenshot")

    def test_only_registered_real_image_is_used(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "meta/real/ad-set/step-5.png"
            image.parent.mkdir(parents=True)
            # 测试用一像素 PNG 只存在于临时目录，不进入公开教程素材。
            image.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg=="))
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"screenshots": [{"platform": "meta_ads", "topic": "Ad Set",
                "variant": "Ad Set Duplicate", "step_number": 5, "path": "meta/real/ad-set/step-5.png",
                "image_source": "meta_official", "source_url": "https://www.facebook.com/business/help/example",
                "captured_at": "2026-11-06", "rights_cleared": True, "cropped_to_step": True}]}), encoding="utf-8")
            with patch("tools.tutorial_screenshots.MANIFEST", manifest), patch("tools.tutorial_screenshots.IMAGE_ROOT", root):
                result = screenshots_for("meta_ads", "Ad Set", "Ad Set Duplicate")
            self.assertEqual(result[5]["image_type"], "real_screenshot")
            self.assertEqual(result[5]["image_source"], "meta_official")

    def test_teaching_request_uses_read_only_steps(self):
        # “怎么创建”表达学习意图，不应被模型误选为真实账户创建操作。
        with patch("agents.ads_learning_agent.choose_action") as choose_action, \
                patch("agents.ads_learning_agent.record_learning", return_value={"success": True}), \
                patch("agents.ads_learning_agent.update_short_term"):
            result = run_ads_learning_agent("Google Ads Campaign 怎么创建？")
        choose_action.assert_not_called()
        self.assertTrue(result["success"])
        self.assertIn("第 1 步：", result["answer"])
        self.assertIn("第 9 步：", result["answer"])


if __name__ == "__main__":
    unittest.main()
