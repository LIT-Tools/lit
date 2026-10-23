import unittest
from datetime import datetime
from unittest.mock import MagicMock

from jira.exceptions import JIRAError
from tzlocal import get_localzone

from lit.exceptions import JiraIntegrationError
from lit.integrations.jira_push import add_worklog


class FakeWorklog:
    def __init__(self, worklog_id):
        self.id = worklog_id

    def __str__(self):
        return self.id


class TestAddWorklog(unittest.TestCase):
    def setUp(self):
        self.mock_jira = MagicMock()
        self.mock_jira._options = {"rest_api_version": "2"}
        self.issue = "PROJ-123"
        self.time_spent = "1h 30m"
        self.comment = "Работа над задачей"
        self.day = "01.01.2023"
        self.time = "10:00"
        self.expected_start_time = datetime.strptime(
            f"{self.day} {self.time}", "%d.%m.%Y %H:%M"
        ).replace(tzinfo=get_localzone())

    def _call(self, comment=None):
        return add_worklog(
            self.mock_jira,
            self.issue,
            self.time_spent,
            self.comment if comment is None else comment,
            self.day,
            self.time,
        )

    def test_add_worklog_success_v2_uses_string(self):
        expected_id = "worklog-123"
        self.mock_jira.add_worklog.return_value = expected_id

        result_id = self._call()

        self.assertEqual(result_id, expected_id)
        self.mock_jira.add_worklog.assert_called_once_with(
            self.issue,
            timeSpent=self.time_spent,
            comment=self.comment,
            started=self.expected_start_time,
        )

    def test_add_worklog_v3_uses_adf(self):
        self.mock_jira._options = {"rest_api_version": "3"}
        self.mock_jira.add_worklog.return_value = "worklog-123"

        result_id = self._call(comment="line1\nline2")

        self.assertEqual(result_id, "worklog-123")
        kwargs = self.mock_jira.add_worklog.call_args.kwargs
        self.assertEqual(kwargs["comment"]["type"], "doc")
        self.assertEqual(len(kwargs["comment"]["content"]), 2)
        self.assertEqual(
            kwargs["comment"]["content"][0]["content"][0]["text"], "line1"
        )

    def test_worklog_object_is_normalized_to_id(self):
        self.mock_jira.add_worklog.return_value = FakeWorklog("12345")

        self.assertEqual(self._call(), "12345")

    def test_empty_comment_is_not_sent(self):
        self.mock_jira.add_worklog.return_value = "worklog-123"

        self.assertEqual(self._call(comment=""), "worklog-123")
        self.assertNotIn("comment", self.mock_jira.add_worklog.call_args.kwargs)

    def test_jira_404_raises(self):
        self.mock_jira.add_worklog.side_effect = JIRAError(
            status_code=404, text="Задача не найдена"
        )

        with self.assertRaises(JiraIntegrationError) as ctx:
            self._call()

        self.assertIn("404", str(ctx.exception))
        self.assertIn("Задача не найдена", str(ctx.exception))

    def test_jira_401_raises(self):
        self.mock_jira.add_worklog.side_effect = JIRAError(
            status_code=401, text="denied"
        )

        with self.assertRaises(JiraIntegrationError) as ctx:
            self._call()

        self.assertIn("401", str(ctx.exception))
        self.assertIn("API token", str(ctx.exception))

    def test_jira_400_raises(self):
        self.mock_jira.add_worklog.side_effect = JIRAError(
            status_code=400, text="bad comment"
        )

        with self.assertRaises(JiraIntegrationError) as ctx:
            self._call()

        self.assertIn("400", str(ctx.exception))
        self.assertIn("bad comment", str(ctx.exception))

    def test_jira_500_raises(self):
        self.mock_jira.add_worklog.side_effect = JIRAError(
            status_code=500, text="server error"
        )

        with self.assertRaises(JiraIntegrationError) as ctx:
            self._call()

        self.assertIn("500", str(ctx.exception))

    def test_timeout_raises(self):
        self.mock_jira.add_worklog.side_effect = TimeoutError("timeout")

        with self.assertRaises(JiraIntegrationError) as ctx:
            self._call()

        self.assertIn("timeout", str(ctx.exception))

    def test_none_worklog_raises(self):
        self.mock_jira.add_worklog.return_value = None

        with self.assertRaises(JiraIntegrationError) as ctx:
            self._call()

        self.assertIn("ID", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
