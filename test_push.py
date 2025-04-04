import unittest
from unittest.mock import MagicMock
from datetime import datetime
from tzlocal import get_localzone
from jira.exceptions import JIRAError

# Импортируем тестируемые функции
from push import add_worklog


class TestAddWorklog(unittest.TestCase):

    def setUp(self):
        # Создаем мок-объект для jira
        self.mock_jira = MagicMock()

        # Примеры входных данных
        self.issue = "PROJ-123"
        self.time_spent = "1h 30m"
        self.comment = "Работа над задачей"
        self.day = "01.01.2023"
        self.time = "10:00"

        # Ожидаемое время начала
        self.expected_start_time = datetime.strptime(
            f"{self.day} {self.time}",
            "%d.%m.%Y %H:%M"
        ).replace(tzinfo=get_localzone())

    def test_add_worklog_success(self):
        """Тест успешного добавления рабочего журнала"""
        # Настройка мока
        expected_id = "worklog-123"
        self.mock_jira.add_worklog.return_value = expected_id

        # Вызов тестируемой функции
        result_id, error = add_worklog(
            self.mock_jira,
            self.issue,
            self.time_spent,
            self.comment,
            self.day,
            self.time
        )

        # Проверки
        self.assertEqual(result_id, expected_id)
        self.assertIsNone(error)

        # Проверяем вызов метода add_worklog с правильными параметрами
        self.mock_jira.add_worklog.assert_called_once_with(
            self.issue,
            timeSpent=self.time_spent,
            comment=self.comment,
            started=self.expected_start_time
        )

    def test_add_worklog_jira_error(self):
        """Тест ошибки JIRA при добавлении рабочего журнала"""
        # Настройка мока для вызова исключения JIRAError
        error_message = "Задача не найдена"
        self.mock_jira.add_worklog.side_effect = JIRAError(status_code=404, text=error_message)

        # Вызов тестируемой функции
        result_id, error = add_worklog(
            self.mock_jira,
            self.issue,
            self.time_spent,
            self.comment,
            self.day,
            self.time
        )

        # Проверки
        self.assertIsNone(result_id)
        self.assertEqual(error, error_message)

        # Проверяем вызов метода add_worklog с правильными параметрами
        self.mock_jira.add_worklog.assert_called_once()

    def test_add_worklog_general_exception(self):
        """Тест общего исключения при добавлении рабочего журнала"""
        # Настройка мока для вызова общего исключения
        error_message = "Ошибка соединения"
        self.mock_jira.add_worklog.side_effect = Exception(error_message)

        # Вызов тестируемой функции
        result_id, error = add_worklog(
            self.mock_jira,
            self.issue,
            self.time_spent,
            self.comment,
            self.day,
            self.time
        )
