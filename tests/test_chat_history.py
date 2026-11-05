"""聊天持久化接口的无数据库单元测试；真实 PostgreSQL 需配置后再做集成验证。"""

import unittest
from unittest.mock import patch

from fastapi import HTTPException
from api.app import chat, conversation_messages
from api.schemas import ChatRequest

CLIENT = "11111111-1111-4111-8111-111111111111"
CONVERSATION = "22222222-2222-4222-8222-222222222222"


class ChatHistoryTests(unittest.TestCase):
    @patch("api.app.database_configured", return_value=True)
    @patch("api.app.create_conversation", return_value={"id": CONVERSATION})
    @patch("api.app.save_message")
    @patch("api.app.run_ads_learning_agent", return_value={"success": True, "answer": "教学回答", "platform": "meta_ads", "intent": "steps", "execution_mode": "rule_fallback"})
    def test_first_question_creates_conversation_and_saves_both_messages(self, _agent, save, create, _configured):
        result = chat(ChatRequest(message="Meta Ads 教学", client_id=CLIENT))
        self.assertEqual(result["conversation_id"], CONVERSATION)
        create.assert_called_once()
        self.assertEqual(save.call_count, 2)
        self.assertEqual(save.call_args_list[0].args[:4], (CONVERSATION, CLIENT, "user", "Meta Ads 教学"))
        self.assertEqual(save.call_args_list[1].args[:4], (CONVERSATION, CLIENT, "assistant", "教学回答"))

    @patch("api.app.database_configured", return_value=False)
    @patch("api.app.run_ads_learning_agent", return_value={"success": True, "answer": "教学回答"})
    def test_no_database_keeps_chat_available(self, _agent, _configured):
        result = chat(ChatRequest(message="Meta Ads 教学", client_id=CLIENT))
        self.assertTrue(result["success"])
        self.assertEqual(result["warnings"][0]["error_type"], "Database Not Configured")

    @patch("api.app.database_configured", return_value=True)
    @patch("api.app.create_conversation", return_value={"id": CONVERSATION})
    @patch("api.app.save_message", side_effect=RuntimeError("temporary database failure"))
    @patch("api.app.run_ads_learning_agent", return_value={"success": True, "answer": "教学回答"})
    def test_save_failure_does_not_hide_answer(self, _agent, _save, _create, _configured):
        result = chat(ChatRequest(message="Meta Ads 教学", client_id=CLIENT))
        self.assertTrue(result["success"])
        self.assertEqual(result["warnings"][0]["error_type"], "Chat History Save Failed")

    @patch("api.app.database_configured", return_value=True)
    @patch("api.app.get_conversation", return_value=None)
    def test_other_client_cannot_read_messages(self, _get, _configured):
        with self.assertRaises(HTTPException) as error:
            conversation_messages(CONVERSATION, CLIENT)
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
