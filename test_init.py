import unittest
from unittest.mock import patch, mock_open
import io
import configparser

# Импортируем тестируемый модуль.
import init

class TestInitConfig(unittest.TestCase):
    @patch("init.os.makedirs")
    @patch("init.Path.exists", return_value=False)  # Симулируем, что файл конфигурации не существует
    @patch("init.open", new_callable=mock_open)
    @patch("init.questionary.text")
    @patch("init.questionary.password")
    def test_init_config(self, mock_password, mock_text, mock_open_fn, mock_path_exists, mock_makedirs):
        # Задаём заранее ответы для вызовов questionary.text().ask() в том порядке, в котором они вызываются:
        # 1. User email
        # 2. User login
        # 3. Jira login
        # 4. Jira email
        # 5. Jira URL
        # 6. Days to sync для Jira
        # 7. GitLab login
        # 8. GitLab URL
        # 9. GitLab email
        # 10. Days to sync для GitLab
        text_side_effects = [
            "user@example.com",  # User email
            "userlogin",         # User login
            "jiralogin",         # Jira login
            "jira@example.com",  # Jira email
            "https://jira.test.com",  # Jira URL
            "15",                # Days to sync для Jira
            "gitlablogin",       # GitLab login
            "https://gitlab.test.com",  # GitLab URL
            "gitlab@example.com",# GitLab email
            "10"                 # Days to sync для GitLab
        ]
        # Задаём ответы для вызовов questionary.password().ask():
        # 1. Jira password
        # 2. GitLab access token
        password_side_effects = [
            "jirapassword",      # Jira password
            "gitlabtoken"        # GitLab access token
        ]
        mock_text.return_value.ask.side_effect = text_side_effects
        mock_password.return_value.ask.side_effect = password_side_effects

        # Перехватываем вывод в консоль для проверки сообщения о сохранении
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            init.init_config()
            output = fake_out.getvalue()
            self.assertIn("Конфигурация сохранена", output)

        # Проверяем, что файл конфигурации был открыт для записи по нужному пути
        mock_open_fn.assert_called_once_with(init.CONFIG_FILE, "w")
        # Собираем всё, что было записано в файл
        handle = mock_open_fn()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)

        # Читаем полученную конфигурацию из строки
        config = configparser.ConfigParser()
        config.read_string(written_content)

        # Проверяем секцию [user]
        self.assertIn("user", config)
        self.assertEqual(config["user"].get("login"), "userlogin")
        self.assertEqual(config["user"].get("email"), "user@example.com")

        # Проверяем секцию [jira]
        self.assertIn("jira", config)
        self.assertEqual(config["jira"].get("login"), "jiralogin")
        self.assertEqual(config["jira"].get("email"), "jira@example.com")
        self.assertEqual(config["jira"].get("pass"), "jirapassword")
        self.assertEqual(config["jira"].get("url"), "https://jira.test.com")
        self.assertEqual(config["jira"].get("days"), "15")

        # Проверяем секцию [gitlab]
        self.assertIn("gitlab", config)
        self.assertEqual(config["gitlab"].get("login"), "gitlablogin")
        self.assertEqual(config["gitlab"].get("email"), "gitlab@example.com")
        self.assertEqual(config["gitlab"].get("url"), "https://gitlab.test.com")
        self.assertEqual(config["gitlab"].get("token"), "gitlabtoken")
        self.assertEqual(config["gitlab"].get("days"), "10")

if __name__ == "__main__":
    unittest.main()
