"""Тесты иерархии исключений."""
import unittest

from lit.exceptions import (
    ConfigError,
    GitLabIntegrationError,
    JiraIntegrationError,
    LitError,
)


class TestExceptions(unittest.TestCase):
    def test_all_errors_inherit_from_lit_error(self):
        for error in (JiraIntegrationError, GitLabIntegrationError, ConfigError):
            self.assertTrue(issubclass(error, LitError))

    def test_message_is_preserved(self):
        self.assertEqual(str(LitError("boom")), "boom")
        self.assertEqual(str(JiraIntegrationError("jira")), "jira")


if __name__ == "__main__":
    unittest.main()
