import unittest

from app.tts_formatter import TTSFormatter


class TestTTSFormatter(unittest.TestCase):
    def setUp(self) -> None:
        self.formatter = TTSFormatter(
            {
                "pronunciation": {
                    "expand_abbreviations": True,
                    "abbreviation_examples": {
                        "AI": "A I",
                        "DBMS": "D B M S",
                        "API": "A P I",
                    },
                }
            }
        )

    def test_year_conversion(self) -> None:
        output = self.formatter.format("This policy is active for 2026.")
        self.assertIn("twenty twenty-six", output)

    def test_abbreviation_expansion(self) -> None:
        output = self.formatter.format("AI and DBMS can use API integration.")
        self.assertIn("A I", output)
        self.assertIn("D B M S", output)
        self.assertIn("A P I", output)

    def test_emoji_removed(self) -> None:
        output = self.formatter.format("Please confirm this now 🙂")
        self.assertNotIn("🙂", output)


if __name__ == "__main__":
    unittest.main()
