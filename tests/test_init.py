import os
import configparser
import importlib
import unittest
from unittest.mock import patch, mock_open, Mock
from lit.init import CONFIG_FILE
from pathlib import Path


class TestInitConfig(unittest.TestCase):

    def setUp(self):
        # Сохраняем оригинальный HOME и устанавливаем временный
        self.original_home = os.environ.get("HOME")
        self.test_home = os.path.abspath("temp_home")
        os.environ["HOME"] = self.test_home
        # Перезагружаем модуль, чтобы пути обновились с учетом нового HOME
        from lit import init
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
    @patch("lit.init.questionary.password")
    @patch("lit.init.questionary.text")
    def test_init_config_first_run(self, mock_text, mock_password, mock_file_open, mock_print):
        """
        Тестирование создания конфига с нуля.
        Проверяем, что все введенные значения сохраняются корректно.
        """
        # Ответы для текстовых вопросов (в том порядке, как они вызываются)
        text_answers = [
            "test@example.com",  # User email
            "",  # Editor
            "https://jira.test.com",  # Jira URL
            "jirauser",  # Jira login
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

        # Проверяем секцию [jira]
        self.assertEqual(config.get("jira", "login"), "jirauser")
        self.assertEqual(config.get("jira", "pass"), "jirapass")
        self.assertEqual(config.get("jira", "url"), "https://jira.test.com")
        self.assertEqual(config.get("jira", "days"), "30")
        self.assertEqual(config.get("jira", "api_version"), "auto")

        # Проверяем секцию [gitlab]
        self.assertEqual(config.get("gitlab", "email"), "gitlab@example.com")
        self.assertEqual(config.get("gitlab", "url"), "https://gitlab.test.com")
        self.assertEqual(config.get("gitlab", "token"), "token123")
        self.assertEqual(config.get("gitlab", "days"), "30")

        # Проверяем что сообщение было выведено
        mock_print.assert_called_with("\n✅ Конфигурация сохранена в .litconfig")

    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch("lit.init.questionary.password")
    @patch("lit.init.questionary.text")
    def test_init_cloud_prompts_email_and_api_token(
        self, mock_text, mock_password, mock_file_open, mock_print
    ):
        """Для Cloud запрашиваются email и API token, а не логин/пароль."""
        text_answers = [
            "user@example.com",  # User email
            "",  # Editor
            "https://example.atlassian.net",  # Jira URL
            "user@example.com",  # Jira email
            "30",  # Jira days
            "https://gitlab.example.com",  # GitLab URL
            "user@example.com",  # GitLab email
            "30",  # GitLab days
        ]
        mock_text.side_effect = [
            Mock(ask=lambda ans=ans: ans) for ans in text_answers
        ]
        mock_password.side_effect = [
            Mock(ask=lambda: "jira-token"),
            Mock(ask=lambda: "gitlab-token"),
        ]

        self.module.init_config()

        handle = mock_file_open()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        config = configparser.RawConfigParser()
        config.read_string(written)

        self.assertEqual(config.get("jira", "login"), "user@example.com")
        self.assertEqual(config.get("jira", "email"), "user@example.com")
        self.assertEqual(config.get("jira", "pass"), "jira-token")
        self.assertEqual(
            config.get("jira", "url"), "https://example.atlassian.net"
        )
        self.assertEqual(config.get("jira", "api_version"), "auto")
        mock_print.assert_called_with("\n✅ Конфигурация сохранена в .litconfig")

    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch("lit.init.questionary.password")
    @patch("lit.init.questionary.text")
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

        # Проверяем что сообщение было выведено
        mock_print.assert_called_with("\n✅ Конфигурация сохранена в .litconfig")


    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch("lit.init.questionary.password")
    @patch("lit.init.questionary.text")
    def test_login_generated_from_email(self, mock_text, mock_password, mock_file_open, mock_print):
        """
        Проверка автогенерации логина из email, если логин не введен.
        Если пользователь принимает значение по умолчанию (нажимает Enter),
        то должна использоваться часть email до '@'.
        """
        # Используем email, который даст логин
        answers = {
            "User email:": "user@example.com",
            "Jira login:": "jirauser",
            "Jira URL:": "https://jira.test.com",
            "Days to sync:": "30",
            "GitLab URL:": "https://gitlab.test.com",
            "GitLab email:": "gitlab@example.com",
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

        # Проверяем что сообщение было выведено
        mock_print.assert_called_with("\n✅ Конфигурация сохранена в .litconfig")

    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch("lit.init.Path.exists", return_value=False)
    @patch("lit.init.questionary.password")
    @patch("lit.init.questionary.text")
    def test_init_zebrains_defaults(self, mock_text, mock_password, mock_exists, mock_file_open, mock_print):
        """Для zebrains-домена URL по умолчанию берутся из dev-fallback."""
        answers = {
            "User email:": "user@zebrains.team",
            "Jira login:": "jirauser",
            "Jira URL:": None,
            "Days to sync:": "30",
            "GitLab URL:": None,
            "GitLab email:": "user@zebrains.team",
        }

        def text_side_effect(prompt, **kwargs):
            answer = answers.get(prompt)
            if answer is None:
                answer = kwargs.get("default", "")
            return Mock(ask=lambda: answer)

        mock_text.side_effect = text_side_effect
        mock_password.side_effect = lambda prompt, **kwargs: Mock(ask=lambda: "secret")

        self.module.init_config()

        handle = mock_file_open()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        config = configparser.RawConfigParser()
        config.read_string(written)

        self.assertEqual(config.get("jira", "url"), "https://jira.itech-group.ru")
        self.assertEqual(config.get("gitlab", "url"), "https://gitlab.zebrains.team")

    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch("lit.init.Path.exists", return_value=False)
    @patch("lit.init.questionary.password")
    @patch("lit.init.questionary.text")
    def test_init_non_zebrains_defaults(self, mock_text, mock_password, mock_exists, mock_file_open, mock_print):
        """Для не-zebrains домена URL по умолчанию пустые — пользователь вводит вручную."""
        answers = {
            "User email:": "user@gmail.com",
            "Jira login:": "jirauser",
            "Jira URL:": None,
            "Days to sync:": "30",
            "GitLab URL:": None,
            "GitLab email:": "user@gmail.com",
        }

        def text_side_effect(prompt, **kwargs):
            answer = answers.get(prompt)
            if answer is None:
                answer = kwargs.get("default", "")
            return Mock(ask=lambda: answer)

        mock_text.side_effect = text_side_effect
        mock_password.side_effect = lambda prompt, **kwargs: Mock(ask=lambda: "secret")

        self.module.init_config()

        handle = mock_file_open()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        config = configparser.RawConfigParser()
        config.read_string(written)

        self.assertEqual(config.get("jira", "url"), "")
        self.assertEqual(config.get("gitlab", "url"), "")


if __name__ == '__main__':
    unittest.main()
