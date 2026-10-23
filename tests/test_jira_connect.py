"""Тесты подключения к Jira и границы CLI для LitError."""
import io
import unittest
from unittest.mock import patch

from jira.exceptions import JIRAError

from lit import cli
from lit.exceptions import JiraIntegrationError
from lit.integrations.jira import load_tasks_from_jira
from lit.integrations.jira_push import jira_connect


class TestJiraConnect(unittest.TestCase):
    def _cfg(self):
        return {
            "url": "https://example.atlassian.net",
            "login": "u@example.com",
            "pass": "token",
            "days": 30,
        }

    @patch("builtins.print")
    @patch("lit.integrations.jira_push.get_jira")
    @patch("lit.integrations.jira_push.JIRA")
    def test_connect_raises_on_failure(self, mock_jira_cls, mock_get_jira, _print):
        mock_get_jira.return_value = self._cfg()
        mock_jira_cls.side_effect = Exception("boom")

        with self.assertRaises(JiraIntegrationError) as ctx:
            jira_connect()

        self.assertIn("boom", str(ctx.exception))

    @patch("builtins.print")
    @patch("lit.integrations.jira_push.get_jira")
    @patch("lit.integrations.jira_push.JIRA")
    def test_connect_raises_on_check_failure(
        self, mock_jira_cls, mock_get_jira, _print
    ):
        mock_get_jira.return_value = self._cfg()
        mock_jira_cls.return_value.server_info.side_effect = Exception("auth failed")

        with self.assertRaises(JiraIntegrationError):
            jira_connect()

    @patch("builtins.print")
    @patch("lit.integrations.jira_push.get_jira")
    @patch("lit.integrations.jira_push.JIRA")
    def test_connect_returns_client(self, mock_jira_cls, mock_get_jira, _print):
        mock_get_jira.return_value = self._cfg()
        client = mock_jira_cls.return_value
        client.server_info.return_value = {"version": "1001.0.0"}
        client.current_user.return_value = "account-id"

        self.assertIs(jira_connect(), client)


class TestLoadTasksFromJiraErrors(unittest.TestCase):
    def _cfg(self):
        return {
            "url": "https://example.atlassian.net",
            "login": "u@example.com",
            "pass": "token",
            "days": 30,
        }

    @patch("lit.integrations.jira.pars_error_jira")
    @patch("lit.integrations.jira.JIRA")
    @patch("lit.integrations.jira.get_jira")
    def test_raises_on_connect_failure(self, mock_get_jira, mock_jira_cls, mock_pars):
        mock_get_jira.return_value = self._cfg()
        mock_jira_cls.side_effect = JIRAError(status_code=401, text="denied")

        with self.assertRaises(JiraIntegrationError):
            load_tasks_from_jira()

        mock_pars.assert_called_once()

    @patch("lit.integrations.jira.pars_error_jira")
    @patch("lit.integrations.jira.JIRA")
    @patch("lit.integrations.jira.get_jira")
    def test_raises_on_auth_check_failure(
        self, mock_get_jira, mock_jira_cls, mock_pars
    ):
        mock_get_jira.return_value = self._cfg()
        mock_jira_cls.return_value.server_info.side_effect = JIRAError(
            status_code=401, text="denied"
        )

        with self.assertRaises(JiraIntegrationError):
            load_tasks_from_jira()

        mock_pars.assert_called_once()


class TestCliErrorBoundary(unittest.TestCase):
    @patch("lit.process_arguments", side_effect=JiraIntegrationError("boom"))
    def test_cli_exits_on_lit_error(self, _process_arguments):
        with patch("sys.stderr", new_callable=io.StringIO) as stderr:
            with self.assertRaises(SystemExit) as ctx:
                cli()

        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("boom", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
