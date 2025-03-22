import os
import configparser
import importlib
import unittest
from io import StringIO
from unittest.mock import patch, mock_open, Mock
from init import init_config, LIT_DIR, CONFIG_FILE


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
    def test_init_config_with_existing_config(self, mock_text, mock_password, mock_file_open):
        """
        Тестирование обновления существующего конфига.
        Проверяем, что дефолтные значения берутся из старого конфига.
        """
        # Создаем существующий конфиг с начальными значениями
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
        # Записываем существующий конфиг через мок (эмулируем, что файл уже существует)
        m = mock_file_open()
        existing_config.write(m)
        # Сбрасываем историю вызовов, чтобы далее отследить вызовы init_config
        mock_file_open.reset_mock()

        # Мокаем questionary так, чтобы возвращались значения по умолчанию (эмуляция нажатия Enter)
        def text_side_effect(*args, **kwargs):
            default_val = kwargs.get("default", "")
            mock_obj = Mock()
            mock_obj.ask.return_value = default_val
            return mock_obj

        def password_side_effect(*args, **kwargs):
            default_val = kwargs.get("default", "")
            mock_obj = Mock()
            mock_obj.ask.return_value = default_val
            return mock_obj

        mock_text.side_effect = text_side_effect
        mock_password.side_effect = password_side_effect

        # Вызываем init_config, который должен использовать существующие дефолты
        self.module.init_config()

        # Получаем содержимое записанного конфига после обновления
        handle = mock_file_open()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        config_new = configparser.RawConfigParser()
        config_new.read_string(written)

        # Проверяем, что значения остались старыми
        self.assertEqual(config_new.get("user", "email"), "old@example.com")
        self.assertEqual(config_new.get("user", "login"), "olduser")
        self.assertEqual(config_new.get("jira", "login"), "oldjira")
        self.assertEqual(config_new.get("jira", "pass"), "oldpass")
        self.assertEqual(config_new.get("jira", "email"), "oldjira@example.com")
        self.assertEqual(config_new.get("jira", "url"), "https://old.jira")
        self.assertEqual(config_new.get("jira", "days"), "60")
        self.assertEqual(config_new.get("gitlab", "login"), "oldgitlab")
        self.assertEqual(config_new.get("gitlab", "email"), "oldgitlab@example.com")
        self.assertEqual(config_new.get("gitlab", "url"), "https://old.gitlab")
        self.assertEqual(config_new.get("gitlab", "token"), "oldtoken")
        self.assertEqual(config_new.get("gitlab", "days"), "90")

    @patch("builtins.open", new_callable=mock_open)
    @patch("init.questionary.password")
    @patch("init.questionary.text")
    def test_login_generated_from_email(self, mock_text, mock_password, mock_file_open):
        """
        Проверка автогенерации логина из email, если логин не введен.
        Если пользователь вводит пустую строку для логина,
        то должна использоваться часть email до '@'.
        """
        # Используем email, который даст логин "s.kushnarev"
        answers = {
            "User email:": "s.kushnarev@example.com",
            "User login:": "",  # Пользователь вводит пустую строку
            "Jira login:": "jirauser",
            "Jira email:": "jira@example.com",
            "Jira URL:": "https://jira.test.com",
            "Days to sync:": "30",
            "GitLab login:": "gitlabuser",
            "GitLab URL:": "https://gitlab.test.com",
            "GitLab email:": "gitlab@example.com",
            "Days to sync:": "30"
        }

        # Функция-обёртка для questionary.text
        def text_side_effect(prompt, **kwargs):
            return Mock(ask=lambda: answers.get(prompt, ""))

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
        self.assertEqual(config.get("user", "login"), "s.kushnarev")

    @patch("builtins.open", new_callable=mock_open)
    @patch("init.questionary.password")
    @patch("init.questionary.text")
    def test_email_validation(self, mock_text, mock_password, mock_file_open):
        """
        Проверка валидации email: если первый ввод неверный, повторный ввод должен вернуть корректный email.
        """
        # Моки для промпта "User email:"
        email_prompts = [Mock(), Mock()]
        email_prompts[0].ask.return_value = "invalid-email"
        email_prompts[1].ask.return_value = "valid@example.com"

        # Для остальных вопросов возвращаем фиксированные значения.
        remaining = [
            Mock(ask=lambda: "user"),  # User login
            Mock(ask=lambda: "jirauser"),  # Jira login
            Mock(ask=lambda: "jira@example.com"),  # Jira email
            Mock(ask=lambda: "https://jira.test.com"),  # Jira URL
            Mock(ask=lambda: "30"),  # Jira days
            Mock(ask=lambda: "gitlabuser"),  # GitLab login
            Mock(ask=lambda: "https://gitlab.test.com"),  # GitLab URL
            Mock(ask=lambda: "gitlab@example.com"),  # GitLab email
            Mock(ask=lambda: "30")  # GitLab days
        ]
        # Устанавливаем side_effect для questionary.text: два вызова для email и затем остальные
        mock_text.side_effect = email_prompts + remaining
        mock_password.return_value = Mock(ask=lambda: "pass")

        self.module.init_config()

        handle = mock_file_open()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        config = configparser.RawConfigParser()
        config.read_string(written)
        # Ожидается, что итоговый email будет корректным
        self.assertEqual(config.get("user", "email"), "valid@example.com")

        # Проверяем, что промпт "User email:" был вызван дважды
        email_calls = [call for call in mock_text.call_args_list if call[0][0] == "User email:"]
        self.assertEqual(len(email_calls), 2)


if __name__ == '__main__':
    unittest.main()
