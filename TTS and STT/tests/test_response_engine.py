import unittest

from app.response_engine import TemplateResponseEngine


class TestResponseEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = TemplateResponseEngine(
            {"preferred_openers": ["Sure, I will help you with that."]}
        )

    def test_infer_instructional_tone(self) -> None:
        tone = self.engine.infer_tone("How do I reset my password?")
        self.assertEqual(tone, "instructional")

    def test_infer_error_tone(self) -> None:
        tone = self.engine.infer_tone("Payment failed and it is not working")
        self.assertEqual(tone, "error_handling")

    def test_generate_alert_response(self) -> None:
        reply, tone = self.engine.generate("This is urgent, what should I do?")
        self.assertEqual(tone, "alert")
        self.assertIn("important", reply.lower())


if __name__ == "__main__":
    unittest.main()
