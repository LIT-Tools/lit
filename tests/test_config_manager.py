"""Тесты чтения секции [jira] из конфига."""
import unittest
from configparser import RawConfigParser

from lit.config_manager import get_jira


class TestGetJira(unittest.TestCase):
    def _cfg(self, **jira):
        cfg = RawConfigParser()
        cfg.add_section("jira")
        for key, value in jira.items():
            cfg.set("jira", key, value)
        return cfg

    def test_defaults(self):
        result = get_jira(self._cfg())

        self.assertEqual(result["login"], "")
        self.assertEqual(result["email"], "")
        self.assertEqual(result["pass"], "")
        self.assertEqual(result["url"], "")
        self.assertEqual(result["days"], 30)
        self.assertEqual(result["api_version"], "auto")

    def test_email_is_fallback_for_login(self):
        result = get_jira(
            self._cfg(**{"email": "u@example.com", "pass": "token"})
        )

        self.assertEqual(result["login"], "u@example.com")
        self.assertEqual(result["email"], "u@example.com")

    def test_login_is_fallback_for_email(self):
        result = get_jira(self._cfg(login="user"))

        self.assertEqual(result["login"], "user")
        self.assertEqual(result["email"], "user")

    def test_explicit_api_version_and_days(self):
        result = get_jira(self._cfg(api_version="3", days="60"))

        self.assertEqual(result["api_version"], "3")
        self.assertEqual(result["days"], 60)

    def test_api_version_is_normalized(self):
        result = get_jira(self._cfg(api_version=" AUTO "))

        self.assertEqual(result["api_version"], "auto")

    def test_invalid_api_version_is_returned_for_client_validation(self):
        result = get_jira(self._cfg(api_version="4"))

        self.assertEqual(result["api_version"], "4")


if __name__ == "__main__":
    unittest.main()
