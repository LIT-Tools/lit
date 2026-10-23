"""Тесты pull-а Jira: currentUser(), пагинация и ошибки."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from jira.exceptions import JIRAError

from lit.exceptions import JiraIntegrationError
from lit.integrations.jira import load_tasks_from_jira


def make_issue(key, summary):
    return SimpleNamespace(key=key, fields=SimpleNamespace(summary=summary))


class TestLoadTasksFromJira(unittest.TestCase):
    def setUp(self):
        self.config = {
            "url": "https://example.atlassian.net",
            "login": "u@example.com",
            "email": "u@example.com",
            "pass": "token",
            "days": 30,
        }
        self.jira = MagicMock()
        self.jira._options = {"rest_api_version": "3"}
        self.jira._is_cloud = True
        self.jira.server_info.return_value = {"version": "1001.0.0"}
        self.jira.current_user.return_value = "account-id"

        patcher = patch(
            "lit.integrations.jira.get_jira", return_value=self.config
        )
        self.mock_get_jira = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "lit.integrations.jira.build_jira", return_value=self.jira
        )
        self.mock_build = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("lit.integrations.jira.save_commits")
        self.mock_save = patcher.start()
        self.addCleanup(patcher.stop)

    def test_cloud_uses_current_user_and_enhanced_search(self):
        self.jira.enhanced_search_issues.side_effect = [
            [make_issue("A-1", "One")],
            [make_issue("A-2", "Two"), make_issue("A-1", "One")],
        ]

        with patch("builtins.print"):
            load_tasks_from_jira()

        self.mock_build.assert_called_once_with(self.config)
        self.assertEqual(self.jira.enhanced_search_issues.call_count, 2)

        first_jql = self.jira.enhanced_search_issues.call_args_list[0].args[0]
        second_jql = self.jira.enhanced_search_issues.call_args_list[1].args[0]
        self.assertIn("assignee = currentUser()", first_jql)
        self.assertIn("worklogAuthor = currentUser()", second_jql)

        for call in self.jira.enhanced_search_issues.call_args_list:
            self.assertFalse(call.kwargs["maxResults"])

        self.mock_save.assert_called_once_with({"A-1": "One", "A-2": "Two"})

    def test_data_center_uses_search_issues(self):
        self.jira._is_cloud = False
        self.jira._options = {"rest_api_version": "2"}
        self.jira.search_issues.side_effect = [
            [make_issue("D-1", "DC")],
            [],
        ]

        with patch("builtins.print"):
            load_tasks_from_jira()

        self.assertEqual(self.jira.search_issues.call_count, 2)
        for call in self.jira.search_issues.call_args_list:
            self.assertFalse(call.kwargs["maxResults"])
        self.mock_save.assert_called_once_with({"D-1": "DC"})

    def test_empty_result_saves_empty_dict(self):
        self.jira.enhanced_search_issues.return_value = []

        with patch("builtins.print"):
            load_tasks_from_jira()

        self.mock_save.assert_called_once_with({})

    def test_search_error_is_raised(self):
        self.jira.enhanced_search_issues.side_effect = JIRAError(
            status_code=400, text="bad jql"
        )

        with patch("builtins.print"):
            with self.assertRaises(JiraIntegrationError):
                load_tasks_from_jira()

        self.mock_save.assert_not_called()

    def test_current_user_fallback_to_email(self):
        self.jira.current_user.side_effect = Exception("no current user")
        self.jira.enhanced_search_issues.return_value = []

        with patch("builtins.print"):
            load_tasks_from_jira()

        first_jql = self.jira.enhanced_search_issues.call_args_list[0].args[0]
        second_jql = self.jira.enhanced_search_issues.call_args_list[1].args[0]
        self.assertIn('assignee = "u@example.com"', first_jql)
        self.assertIn('worklogAuthor = "u@example.com"', second_jql)

    def test_no_user_and_no_fallback_raises(self):
        self.jira.current_user.side_effect = Exception("no current user")
        self.config.pop("email")
        self.config.pop("login")

        with patch("builtins.print"):
            with self.assertRaises(JiraIntegrationError):
                load_tasks_from_jira()

        self.jira.enhanced_search_issues.assert_not_called()
        self.mock_save.assert_not_called()

    def test_server_info_error_is_raised(self):
        self.jira.server_info.side_effect = JIRAError(
            status_code=401, text="denied"
        )

        with patch("builtins.print"):
            with self.assertRaises(JiraIntegrationError) as ctx:
                load_tasks_from_jira()

        self.assertIn("401", str(ctx.exception))
        self.mock_save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
