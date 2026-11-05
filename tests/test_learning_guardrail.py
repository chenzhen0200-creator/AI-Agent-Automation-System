"""教学问题允许只读工具，明确代执行请求仍被拦截。"""

import unittest
from unittest.mock import patch

from agents.ads_learning_agent import detect_platform, run_ads_learning_agent
from guardrails.risk_classifier import classify_risk


class LearningGuardrailTests(unittest.TestCase):
    def test_platform_aliases(self):
        for question in ("FB广告", "fb广告组", "Facebook Ad Set", "IG广告"):
            with self.subTest(question=question):
                self.assertEqual(detect_platform(question), "meta_ads")

    def test_learning_requests_use_steps(self):
        cases = (
            "怎么在FB的同一个广告系列复制添加另一个广告组",
            "FB广告组在哪里",
            "Meta怎么复制Ad Set",
            "怎么删除一个Meta广告组",
            "Google Ads怎么创建广告系列",
            "怎么修改Google Ads预算",
        )
        with patch("agents.ads_learning_agent.record_learning", return_value={"success": True}), \
                patch("agents.ads_learning_agent.update_short_term"), \
                patch("agents.ads_learning_agent.choose_action") as model:
            for question in cases:
                with self.subTest(question=question):
                    result = run_ads_learning_agent(question)
                    self.assertTrue(result["success"])
                    self.assertEqual(result["intent"], "steps")
                    self.assertTrue(any(item["tool_name"] in ("get_meta_ads_steps", "get_google_ads_steps")
                                        for item in result["tool_results"]))
            model.assert_not_called()

    def test_direct_account_changes_stay_blocked(self):
        for question in (
            "帮我直接删除这个广告组",
            "替我把预算改成100美元",
            "直接在我的Meta账户创建Campaign",
            "帮我发布这个广告",
        ):
            with self.subTest(question=question):
                result = run_ads_learning_agent(question)
                self.assertFalse(result["success"])
                self.assertEqual(result["error_type"], "High Risk Action Blocked")

    def test_model_topic_cannot_upgrade_learning_request(self):
        risk = classify_risk("get_meta_ads_steps", "怎么复制广告组？", {"topic": "直接删除真实广告组"})
        self.assertNotEqual(risk["risk_level"], "high")


if __name__ == "__main__":
    unittest.main()
