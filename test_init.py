import os
import configparser
import importlib
import unittest
from unittest.mock import patch, mock_open, Mock
from init import CONFIG_FILE
from collections import deque
from pathlib import Path


class TestInitConfig(unittest.TestCase):

    def setUp(self):
        # Сохраняем оригинальный HOME и устанавливаем временный
        self.original_home = os.environ.get("HOME")
        self.test_home = os.path.abspath("temp_home")
        os.environ["HOME"] = self.test_home
        # Перезагружаем модуль, чтобы пути обновились с учетом нового HOME
        import init
        importlib.reload(init)
        self.module = init

    def tearDown(self):
        # Восстанавливаем оригинальный HOME
        if self.original_home is not None:
            os.environ["HOME"] = self.original_home
        else:
            del os.environ["HOME"]

    @patch("init.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("init.questionary.password")
    @patch("init.questionary.text")
    def test_init_config_first_run(self, mock_text, mock_password, mock_file_open, mock_makedirs):
        """
        Тестирование создания конфига с нуля.
        Проверяем, что все введенные значения сохраняются корректно.
        """
        # Ответы для текстовых вопросов (в том порядке, как они вызываются)
        text_answers = [
            "test@example.com",  # User email
            "testuser",  # User login
            "jirauser",  # Jira login
            "jira@example.com",  # Jira email
            "https://jira.test.com",  # Jira URL
            "30",  # Jira days
            "gitlabuser",  # GitLab login
            "https://gitlab.test.com",  # GitLab URL
            "gitlab@example.com",  # GitLab email
            "30"  # GitLab days
        ]
        # Для каждого ответа создаем мок, который при вызове ask() возвращает нужное значение
        mock_text.side_effect = [Mock(ask=lambda ans=ans: ans) for ans in text_answers]

        # Ответы для password вопросов
        password_answers = ["jirapass", "token123"]
        mock_password.side_effect = [Mock(ask=lambda ans=ans: ans) for ans in password_answers]

        # Вызываем тестируемую функцию
        self.module.init_config()

        # Получаем содержимое, записанное в конфиг
        handle = mock_file_open()
        written = "".join(call.args[0] for call in handle.write.call_args_list)

        # Читаем конфигурацию из записанной строки
        config = configparser.RawConfigParser()
        config.read_string(written)

        # Проверяем секцию [user]
        self.assertEqual(config.get("user", "email"), "test@example.com")
        self.assertEqual(config.get("user", "login"), "testuser")

        # Проверяем секцию [jira]
        self.assertEqual(config.get("jira", "login"), "jirauser")
        self.assertEqual(config.get("jira", "pass"), "jirapass")
        self.assertEqual(config.get("jira", "email"), "jira@example.com")
        self.assertEqual(config.get("jira", "url"), "https://jira.test.com")
        self.assertEqual(config.get("jira", "days"), "30")

        # Проверяем секцию [gitlab]
        self.assertEqual(config.get("gitlab", "login"), "gitlabuser")
        self.assertEqual(config.get("gitlab", "email"), "gitlab@example.com")
        self.assertEqual(config.get("gitlab", "url"), "https://gitlab.test.com")
        self.assertEqual(config.get("gitlab", "token"), "token123")
        self.assertEqual(config.get("gitlab", "days"), "30")

    @patch("builtins.open", new_callable=mock_open)
    @patch("init.questionary.password")
    @patch("init.questionary.text")
    @patch.object(Path, "exists", return_value=True)  # Мокаем проверку существования файла
    def test_init_config_with_existing_config(self, mock_exists, mock_text, mock_password, mock_file_open):
        """
        Тестирование обновления существующего конфига.
        """
        # Эмулируем существующий конфиг
        existing_config = configparser.ConfigParser()
        existing_config["user"] = {"email": "old@example.com", "login": "olduser"}
        existing_config["jira"] = {
            "login": "oldjira",
            "pass": "oldpass",
            "email": "oldjira@example.com",
            "url": "https://old.jira",
            "days": "60"
        }
        existing_config["gitlab"] = {
            "login": "oldgitlab",
            "email": "oldgitlab@example.com",
            "url": "https://old.gitlab",
            "token": "oldtoken",
            "days": "90"
        }

        # Мокаем чтение существующего конфига
        mock_file_open().read.return_value = existing_config.read(CONFIG_FILE)

        # Мокаем questionary для возврата дефолтных значений
        mock_text.side_effect = lambda prompt, **kwargs: Mock(ask=lambda: kwargs.get("default", ""))
        mock_password.side_effect = lambda prompt, **kwargs: Mock(ask=lambda: kwargs.get("default", ""))

        self.module.init_config()

        # Проверяем, что default.read(CONFIG_FILE) был вызван
        mock_exists.assert_called_once()  # Убедимся, что проверка существования файла прошла

    @patch("builtins.open", new_callable=mock_open)
    @patch("init.questionary.password")
    @patch("init.questionary.text")
    def test_login_generated_from_email(self, mock_text, mock_password, mock_file_open):
        """
        Проверка автогенерации логина из email, если логин не введен.
        Если пользователь принимает значение по умолчанию (нажимает Enter),
        то должна использоваться часть email до '@'.
        """
        # Используем email, который даст логин
        answers = {
            "User email:": "user@example.com",
            # Пустой ответ для логина - пользователь нажал Enter (принял дефолт)
            "User login:": None,  # Используем None как индикатор принятия дефолта
            "Jira login:": "jirauser",
            "Jira email:": "jira@example.com",
            "Jira URL:": "https://jira.test.com",
            "Days to sync:": "30",
            "GitLab login:": "gitlabuser",
            "GitLab URL:": "https://gitlab.test.com",
            "GitLab email:": "gitlab@example.com",
            "Days to sync:": "30"
        }

        # Функция-обёртка для questionary.text с учетом default
        def text_side_effect(prompt, **kwargs):
            answer = answers.get(prompt)
            # Если ответ None, используем default из kwargs
            if answer is None:
                answer = kwargs.get('default', '')
            return Mock(ask=lambda: answer)

        mock_text.side_effect = text_side_effect

        password_answers = {
            "Jira password:": "jirapass",
            "GitLab access token:": "gitlabtoken"
        }

        def password_side_effect(prompt, **kwargs):
            return Mock(ask=lambda: password_answers.get(prompt, ""))

        mock_password.side_effect = password_side_effect

        self.module.init_config()

        handle = mock_file_open()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        config = configparser.RawConfigParser()
        config.read_string(written)
        # Ожидается, что логин будет сгенерирован как часть email до '@'
        self.assertEqual(config.get("user", "login"), "user")


@patch("builtins.open", new_callable=mock_open)
@patch("init.questionary.password")
@patch("init.questionary.text")
def test_email_validation(self, mock_text, mock_password, mock_file_open):
    """
    Проверка валидации email: повторный запрос при неверном вводе.
    """
    # Очередь ответов для промптов
    responses = [
        ("User email:", ["invalid-email", "valid@example.com"]),  # Два ответа для email
        ("User login:", ["user"]),
        ("Jira login:", ["jirauser"]),
        ("Jira email:", ["jira@example.com"]),
        ("Jira URL:", ["https://jira.test.com"]),
        ("Days to sync:", ["30"]),
        ("GitLab login:", ["gitlabuser"]),
        ("GitLab URL:", ["https://gitlab.test.com"]),
        ("GitLab email:", ["gitlab@example.com"]),
        ("Days to sync:", ["30"])
    ]

    # Собираем ответы в словарь с очередями
    answer_queues = {prompt: deque(values) for prompt, values in responses}

    def text_side_effect(prompt, **kwargs):
        queue = answer_queues.get(prompt, deque())
        if queue:
            return Mock(ask=lambda: queue.popleft())
        return Mock(ask=lambda: "")

    mock_text.side_effect = text_side_effect
    mock_password.return_value = Mock(ask=lambda: "pass")

    self.module.init_config()

    # Проверка записанного email
    written_config = configparser.RawConfigParser()
    written_config.read_string("".join(
        call.args[0]
        for call in mock_file_open.return_value.write.call_args_list
    ))

    self.assertEqual(written_config.get("user", "email"), "valid@example.com")

    # Проверка количества запросов email
    email_calls = [call[0][0] for call in mock_text.call_args_list if call[0][0] == "User email:"]
    self.assertEqual(len(email_calls), 2, "Должно быть 2 запроса email")


if __name__ == '__main__':
    unittest.main()
