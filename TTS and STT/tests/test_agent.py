import unittest

from app.agent import IndianVoiceAgent


class TestAgent(unittest.TestCase):
    def test_agent_responds_with_metadata(self) -> None:
        agent = IndianVoiceAgent()
        response = agent.respond("Can you help me with account setup?")
        self.assertTrue(response.reply)
        self.assertTrue(response.profile_name)
        self.assertEqual(response.language, "en-IN")
        self.assertTrue(response.reply.endswith((".", "!", "?")))


if __name__ == "__main__":
    unittest.main()
