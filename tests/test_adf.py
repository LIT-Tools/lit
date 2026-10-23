"""Тесты конверсии plain text -> ADF."""
import unittest

from lit.integrations.adf import plain_text_to_adf


class TestPlainTextToADF(unittest.TestCase):
    def test_single_line(self):
        self.assertEqual(
            plain_text_to_adf("hello"),
            {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "hello"}],
                    }
                ],
            },
        )

    def test_multiline(self):
        result = plain_text_to_adf("line1\nline2")
        self.assertEqual(len(result["content"]), 2)
        self.assertEqual(result["content"][0]["content"][0]["text"], "line1")
        self.assertEqual(result["content"][1]["content"][0]["text"], "line2")

    def test_blank_line_becomes_empty_paragraph(self):
        result = plain_text_to_adf("line1\n\nline3")
        self.assertEqual(len(result["content"]), 3)
        self.assertEqual(result["content"][1], {"type": "paragraph"})

    def test_whitespace_only_line_becomes_empty_paragraph(self):
        result = plain_text_to_adf("line1\n   \nline3")
        self.assertEqual(len(result["content"]), 3)
        self.assertEqual(result["content"][1], {"type": "paragraph"})

    def test_empty_text(self):
        self.assertEqual(
            plain_text_to_adf(""),
            {"type": "doc", "version": 1, "content": []},
        )

    def test_crlf_is_normalized(self):
        result = plain_text_to_adf("line1\r\nline2")
        self.assertEqual(len(result["content"]), 2)
        self.assertEqual(result["content"][0]["content"][0]["text"], "line1")
        self.assertEqual(result["content"][1]["content"][0]["text"], "line2")

    def test_leading_spaces_are_preserved(self):
        result = plain_text_to_adf("        indented")
        self.assertEqual(
            result["content"][0]["content"][0]["text"], "        indented"
        )

    def test_special_chars_and_emoji_are_preserved(self):
        text = 'третья строка: <tag> & "quotes" & \'single\'\nэмодзи: 🚀'
        result = plain_text_to_adf(text)
        self.assertEqual(
            result["content"][0]["content"][0]["text"],
            'третья строка: <tag> & "quotes" & \'single\'',
        )
        self.assertEqual(result["content"][1]["content"][0]["text"], "эмодзи: 🚀")

    def test_invalid_control_chars_are_stripped(self):
        result = plain_text_to_adf("a\x00b\x07c")
        self.assertEqual(result["content"][0]["content"][0]["text"], "abc")

    def test_tab_is_preserved(self):
        result = plain_text_to_adf("a\tb")
        self.assertEqual(result["content"][0]["content"][0]["text"], "a\tb")


if __name__ == "__main__":
    unittest.main()
