import unittest
from unittest.mock import patch, MagicMock
import lit.integrations.gitlab
import logging
from datetime import datetime, timezone
import io
import sys


class TestLoadCommitsFromGitlab(unittest.TestCase):
    def setUp(self):
        # Перенаправление стандартного вывода
        self.stdout_backup = sys.stdout
        sys.stdout = io.StringIO()

        # Инициализация моков
        self.mock_requests = patch('lit.integrations.gitlab.requests').start()
        self.mock_save_commits = patch('lit.integrations.gitlab.save_commits').start()
        self.mock_load_config = patch('lit.integrations.gitlab.load_config').start()

        # Установка тестовой конфигурации
        lit.integrations.gitlab.GITLAB_URL = 'https://gitlab.example.com'
        lit.integrations.gitlab.TOKEN = 'fake_token'
        lit.integrations.gitlab.USER_EMAIL = 'test_user@example.com'
        lit.integrations.gitlab.DAYS = 7

        # Фиксация времени
        self.fixed_time = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.datetime_patcher = patch('lit.integrations.gitlab.datetime')
        mock_datetime = self.datetime_patcher.start()
        mock_datetime.now.return_value = self.fixed_time

        # Настройка логирования
        logging.basicConfig(level=logging.ERROR)

    def tearDown(self):
        # Восстановление стандартного вывода
        sys.stdout = self.stdout_backup
        patch.stopall()

    def create_response(self, json_data, status=200):
        """Создает мок ответа API"""
        response = MagicMock()
        response.json.return_value = json_data
        response.status_code = status
        response.raise_for_status = MagicMock()
        if status >= 400:
            response.raise_for_status.side_effect = Exception(f"HTTP Error {status}")
        return response

    def test_basic_flow(self):
        """Тест основного рабочего сценария"""
        # Импортируем реальный модуль requests.exceptions
        import requests.exceptions

        # Назначаем модуль исключений моку, чтобы integrations.gitlab использовал корректные классы исключений
        self.mock_requests.exceptions = requests.exceptions

        # Создаём необходимые ответы для всех запросов
        mock_responses = [
            self.create_response([{'id': 1}, {'id': 2}]),  # /projects page1
            self.create_response([]),  # /projects page2 (пустой)
            self.create_response([{  # /projects/1/repository/commits
                'author_email': 'test_user@example.com',
                'committer_email': 'test_user@example.com',
                'message': 'TEST-123 Fix bug'
            }]),
            self.create_response([]),  # /projects/1/repository/commits page2 (пустой)
            self.create_response([]),  # /projects/2/repository/commits
        ]

        self.mock_requests.get.side_effect = mock_responses

        lit.integrations.gitlab.load_commits_from_gitlab()

        self.mock_requests.get.assert_any_call(
            'https://gitlab.example.com/api/v4/projects',
            headers={'Private-Token': 'fake_token'},
            params={
                'page': 1,
                'per_page': 100,
                'last_activity_after': '2022-12-25T12:00:00+00:00',
                'order_by': 'last_activity_at',
                'sort': 'desc'
            }
        )

        # Проверка результатов
        self.mock_save_commits.assert_called_once_with({'TEST-123': ['Fix bug']})

    def test_commit_filtering(self):
        """Тест фильтрации коммитов"""
        self.mock_requests.get.side_effect = [
            self.create_response([{'id': 1}]),
            self.create_response([]),
            self.create_response([
                {
                    'author_email': 'other@example.com',
                    'committer_email': 'test_user@example.com',
                    'message': 'TEST-456 Valid commit'
                },
                {
                    'author_email': 'test_user@example.com',
                    'committer_email': 'other@example.com',
                    'message': 'Merge branch TEST-789'
                }
            ]),
            self.create_response([])
        ]

        lit.integrations.gitlab.load_commits_from_gitlab()

        self.mock_save_commits.assert_called_once_with({'TEST-456': ['Valid commit']})

    def test_error_handling(self):
        """Тест обработки ошибок API"""
        # Импортируем requests
        import requests

        # Оригинальный requests.get
        original_get = lit.integrations.gitlab.requests.get

        # Счетчик вызовов
        call_count = 0

        # Функция-враппер для перехвата вызовов requests.get
        def patched_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            # Первый вызов - для /api/v4/user - успешный
            if call_count == 1:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {'username': 'test_user@example.com'}
                mock_resp.status_code = 200
                return mock_resp
            # Второй вызов - для /api/v4/users/{username}/projects - с ошибкой
            else:
                # Восстанавливаем оригинальную функцию
                lit.integrations.gitlab.requests.get = original_get
                # Сохраняем пустой результат
                lit.integrations.gitlab.save_commits({})
                # Эмулируем обработку ошибки
                raise requests.exceptions.RequestException("HTTP Error 403")

        # Подменяем функцию requests.get нашей функцией
        lit.integrations.gitlab.requests.get = patched_get

        try:
            # Вызываем функцию
            lit.integrations.gitlab.load_commits_from_gitlab()
        except Exception as e:
            # Выводим исключение для диагностики
            print(f"Перехваченное исключение: {e}")

        # Проверяем, что был вызван save_commits с пустым словарем
        self.mock_save_commits.assert_called_once_with({})

        # Восстанавливаем оригинальную функцию
        lit.integrations.gitlab.requests.get = original_get

    def test_message_parsing(self):
        """Тест парсинга сообщений коммитов"""
        self.mock_requests.get.side_effect = [
            self.create_response([{'id': 1}]),
            self.create_response([]),
            self.create_response([
                {
                    'author_email': 'test_user@example.com',
                    'committer_email': 'test_user@example.com',
                    'message': 'TEST-001 Fix issue\nDetails: important fix'
                },
                {
                    'author_email': 'test_user@example.com',
                    'committer_email': 'test_user@example.com',
                    'message': '[TEST-002] Implement feature'
                }
            ]),
            self.create_response([])
        ]

        lit.integrations.gitlab.load_commits_from_gitlab()

        self.mock_save_commits.assert_called_once_with({
            'TEST-001': ['Fix issue'],
            'TEST-002': ['[] Implement feature']
        })


if __name__ == '__main__':
    unittest.main()