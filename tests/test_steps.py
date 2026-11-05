"""检查教学步骤的覆盖范围与回答完整性。运行：python -m unittest discover -s tests"""

import unittest

from agents.answer_composer import _render
from tools.google_ads_steps_tool import get_google_ads_steps
from tools.meta_ads_steps_tool import get_meta_ads_steps
from tools.google_ads_steps_tool import TOPIC_STEPS as GOOGLE_TOPICS
from tools.meta_ads_steps_tool import TOPIC_STEPS as META_TOPICS


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
            for field in ("title", "ui_location", "action", "description", "expected_result", "image_hint"):
                self.assertTrue(item.get(field), f"{expected_topic}: {field} 不应为空")
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

    def test_answer_contains_every_step_and_field(self):
        result = self.check_topic(get_meta_ads_steps, "Meta Ads 广告组在哪里设置", "Ad Set", 5)
        answer = _render("get_meta_ads_steps", result)
        self.assertIn(f"第 {len(result['steps'])} 步：", answer)
        for label in ("位置：", "操作：", "说明：", "预期结果：", "图示提示："):
            self.assertEqual(answer.count(label), len(result["steps"]))


if __name__ == "__main__":
    unittest.main()
