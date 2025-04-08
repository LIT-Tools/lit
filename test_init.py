import os
import configparser
import importlib
import unittest
from unittest.mock import patch, mock_open, Mock
from init import CONFIG_FILE
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

    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch("init.questionary.password")
    @patch("init.questionary.text")
    def test_init_config_first_run(self, mock_text, mock_password, mock_file_open, mock_print):
        """
        Тестирование создания конфига с нуля.
        Проверяем, что все введенные значения сохраняются корректно.
        """
        # Ответы для текстовых вопросов (в том порядке, как они вызываются)
        text_answers = [
            "test@example.com",  # User email
            "testuser",  # User login
            "", # Editor
            "jirauser",  # Jira login
            "https://jira.test.com",  # Jira URL
            "30",  # Jira days
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
        self.assertEqual(config.get("jira", "url"), "https://jira.test.com")
        self.assertEqual(config.get("jira", "days"), "30")

        # Проверяем секцию [gitlab]
        self.assertEqual(config.get("gitlab", "email"), "gitlab@example.com")
        self.assertEqual(config.get("gitlab", "url"), "https://gitlab.test.com")
        self.assertEqual(config.get("gitlab", "token"), "token123")
        self.assertEqual(config.get("gitlab", "days"), "30")

        # Проверяем что сообщение было выведено
        mock_print.assert_called_with("\n✅ Конфигурация сохранена в .litconfig")

    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch("init.questionary.password")
    @patch("init.questionary.text")
    @patch.object(Path, "exists", return_value=True)  # Мокаем проверку существования файла
    def test_init_config_with_existing_config(self, mock_exists, mock_text, mock_password, mock_file_open, mock_print):
        """
        Тестирование обновления существующего конфига.
        """
        # Эмулируем существующий конфиг
        existing_config = configparser.ConfigParser()
        existing_config["user"] = {"email": "old@example.com", "login": "olduser"}
        existing_config["jira"] = {
            "login": "oldjira",
            "pass": "oldpass",
            "url": "https://old.jira",
            "days": "60"
        }
        existing_config["gitlab"] = {
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

        # Проверяем что сообщение было выведено
        mock_print.assert_called_with("\n✅ Конфигурация сохранена в .litconfig")


    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch("init.questionary.password")
    @patch("init.questionary.text")
    def test_login_generated_from_email(self, mock_text, mock_password, mock_file_open, mock_print):
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
            "Jira URL:": "https://jira.test.com",
            "Days to sync:": "30",
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

        # Проверяем что сообщение было выведено
        mock_print.assert_called_with("\n✅ Конфигурация сохранена в .litconfig")


if __name__ == '__main__':
    unittest.main()
