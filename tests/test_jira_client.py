"""Тесты единого клиента Jira: версия API, подключение, поиск."""
import unittest
from unittest.mock import MagicMock, call, patch

from jira.exceptions import JIRAError

from lit.exceptions import ConfigError, JiraIntegrationError
from lit.integrations.jira_client import (
    build_jira,
    format_jira_error,
    resolve_api_version,
    search_all_issues,
)


class TestResolveApiVersion(unittest.TestCase):
    def test_explicit_versions(self):
        self.assertEqual(resolve_api_version({"api_version": "2"}), "2")
        self.assertEqual(resolve_api_version({"api_version": "3"}), "3")

    def test_auto_without_client(self):
        self.assertEqual(resolve_api_version({"api_version": "auto"}), "auto")
        self.assertEqual(resolve_api_version({}), "auto")

    def test_auto_with_cloud_client(self):
        jira = MagicMock()
        jira._is_cloud = True
        self.assertEqual(resolve_api_version({"api_version": "auto"}, jira), "3")

    def test_auto_with_data_center_client(self):
        jira = MagicMock()
        jira._is_cloud = False
        self.assertEqual(resolve_api_version({"api_version": "auto"}, jira), "2")

    def test_invalid_version(self):
        with self.assertRaises(ConfigError):
            resolve_api_version({"api_version": "4"})


class TestBuildJira(unittest.TestCase):
    def _cfg(self, version="auto"):
        return {
            "url": "https://example.atlassian.net",
            "login": "u@example.com",
            "pass": "token",
            "api_version": version,
        }

    @patch("lit.integrations.jira_client._make_client")
    def test_explicit_version(self, make_client):
        cfg = self._cfg("3")
        client = MagicMock()
        make_client.return_value = client

        self.assertIs(build_jira(cfg), client)
        make_client.assert_called_once_with(cfg, "3")

    @patch("lit.integrations.jira_client._make_client")
    def test_auto_cloud_returns_v3(self, make_client):
        cfg = self._cfg()
        cloud = MagicMock()
        cloud._is_cloud = True
        make_client.return_value = cloud

        self.assertIs(build_jira(cfg), cloud)
        make_client.assert_called_once_with(cfg, "3")

    @patch("lit.integrations.jira_client._make_client")
    def test_auto_data_center_recreates_v2(self, make_client):
        cfg = self._cfg()
        probe = MagicMock()
        probe._is_cloud = False
        dc = MagicMock()
        make_client.side_effect = [probe, dc]

        self.assertIs(build_jira(cfg), dc)
        self.assertEqual(
            make_client.call_args_list,
            [call(cfg, "3"), call(cfg, "2")],
        )

    @patch("lit.integrations.jira_client._make_client")
    def test_auto_data_center_ignores_close_error(self, make_client):
        cfg = self._cfg()
        probe = MagicMock()
        probe._is_cloud = False
        probe.close.side_effect = RuntimeError("close failed")
        dc = MagicMock()
        make_client.side_effect = [probe, dc]

        self.assertIs(build_jira(cfg), dc)

    @patch("lit.integrations.jira_client._make_client")
    def test_auto_falls_back_on_404(self, make_client):
        cfg = self._cfg()
        dc = MagicMock()
        make_client.side_effect = [
            JIRAError(status_code=404, text="not found"),
            dc,
        ]

        self.assertIs(build_jira(cfg), dc)
        self.assertEqual(
            make_client.call_args_list,
            [call(cfg, "3"), call(cfg, "2")],
        )

    @patch("lit.integrations.jira_client._make_client")
    def test_auth_error_is_wrapped(self, make_client):
        make_client.side_effect = JIRAError(status_code=401, text="denied")

        with self.assertRaises(JiraIntegrationError):
            build_jira(self._cfg())

    @patch("lit.integrations.jira_client._make_client")
    def test_unexpected_error_is_wrapped(self, make_client):
        make_client.side_effect = RuntimeError("boom")

        with self.assertRaises(JiraIntegrationError) as ctx:
            build_jira(self._cfg())

        self.assertIn("boom", str(ctx.exception))


class TestSearchAllIssues(unittest.TestCase):
    def test_cloud_uses_enhanced_search(self):
        jira = MagicMock()
        jira._is_cloud = True
        jira.enhanced_search_issues.return_value = ["a", "b"]

        result = search_all_issues(jira, "jql", fields="key")

        jira.enhanced_search_issues.assert_called_once_with(
            "jql", maxResults=False, fields="key"
        )
        self.assertEqual(result, ["a", "b"])

    def test_data_center_uses_search_issues(self):
        jira = MagicMock()
        jira._is_cloud = False
        jira.search_issues.return_value = ["a"]

        result = search_all_issues(jira, "jql")

        jira.search_issues.assert_called_once_with(
            "jql",
            maxResults=False,
            fields="key,summary,status,assignee",
        )
        self.assertEqual(result, ["a"])

    def test_none_result_becomes_empty_list(self):
        jira = MagicMock()
        jira._is_cloud = True
        jira.enhanced_search_issues.return_value = None

        self.assertEqual(search_all_issues(jira, "jql"), [])

    def test_error_is_wrapped(self):
        jira = MagicMock()
        jira._is_cloud = False
        jira.search_issues.side_effect = JIRAError(status_code=400, text="bad")

        with self.assertRaises(JiraIntegrationError):
            search_all_issues(jira, "jql")


class TestFormatJiraError(unittest.TestCase):
    def test_401_mentions_api_token(self):
        message = format_jira_error(JIRAError(status_code=401, text="denied"))
        self.assertIn("401", message)
        self.assertIn("API token", message)

    def test_403_mentions_forbidden(self):
        message = format_jira_error(JIRAError(status_code=403, text="forbidden"))
        self.assertIn("403", message)

    def test_404_mentions_endpoint(self):
        message = format_jira_error(JIRAError(status_code=404, text="not found"))
        self.assertIn("404", message)
        self.assertIn("endpoint", message)

    def test_generic_error(self):
        message = format_jira_error(RuntimeError("boom"))
        self.assertIn("boom", message)

    def test_long_text_is_truncated(self):
        message = format_jira_error(JIRAError(status_code=500, text="x" * 600))
        self.assertIn("…", message)
        self.assertLessEqual(len(message), 530)


class TestMakeClient(unittest.TestCase):
    @patch("lit.integrations.jira_client.JIRA")
    def test_uses_login_and_version_options(self, jira_cls):
        from lit.integrations.jira_client import _make_client

        client = _make_client(
            {"url": "https://example.atlassian.net", "login": "u", "pass": "p"},
            "3",
        )

        jira_cls.assert_called_once_with(
            server="https://example.atlassian.net",
            basic_auth=("u", "p"),
            options={
                "server": "https://example.atlassian.net",
                "rest_api_version": "3",
                "verify": True,
            },
            timeout=20,
        )
        self.assertIs(client, jira_cls.return_value)

    @patch("lit.integrations.jira_client.JIRA")
    def test_falls_back_to_email(self, jira_cls):
        from lit.integrations.jira_client import _make_client

        _make_client({"url": "https://example.atlassian.net", "email": "e", "pass": "p"}, "2")

        self.assertEqual(jira_cls.call_args.kwargs["basic_auth"], ("e", "p"))


class TestCreateClient(unittest.TestCase):
    @patch("lit.integrations.jira_client._make_client")
    def test_wraps_jira_error(self, make_client):
        from lit.integrations.jira_client import _create_client

        make_client.side_effect = JIRAError(status_code=401, text="denied")

        with self.assertRaises(JiraIntegrationError):
            _create_client({"url": "https://example.atlassian.net"}, "3")

    @patch("lit.integrations.jira_client._make_client")
    def test_wraps_unexpected_error(self, make_client):
        from lit.integrations.jira_client import _create_client

        make_client.side_effect = RuntimeError("boom")

        with self.assertRaises(JiraIntegrationError) as ctx:
            _create_client({"url": "https://example.atlassian.net"}, "3")

        self.assertIn("boom", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
