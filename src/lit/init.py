import configparser
import os
import questionary
from configparser import ConfigParser
from pathlib import Path
from lit.constants import LIT_DIR, COMMITS_FILE, CONFIG_FILE

os.makedirs(LIT_DIR, exist_ok=True)


def init_config():
    """Интерактивная настройка конфигурации"""
    config = ConfigParser()

    # Проверяем существующий конфиг для дефолтных значений
    default = ConfigParser()
    if Path(CONFIG_FILE).exists():
        default.read(CONFIG_FILE)

    # Секция [user]
    user_email = questionary.text(
        "User email:",
        default=default.get("user", "email", fallback=""),
        validate=lambda val: "@" in val or "Email обязателен"
    ).ask()

    editor = questionary.text(
        "Editor:",
        default=default.get("user", "editor", fallback=""),
        instruction="\n  [Команда или путь до текстового редактора для команды edit (не обязательно)]"
    ).ask()

    config["user"] = {
        "email": user_email,
        "editor": editor
    }

    # Секция [jira]
    # Zebrains-домен (определяем из email до вопросов)
    is_zebrains_user = "zebrains" in (user_email.split("@")[1] if "@" in user_email else "")
    jira_url_default = "https://jira.zebrains.team" if is_zebrains_user else "https://jira.itech-group.ru"
    
    jira_login = questionary.text(
        "Jira login:",
        default=default.get("jira", "login", fallback=user_email.split("@")[0] if "@" in user_email else "")
    ).ask()
    # TODO API token пока почему то не срабатывает, нужно разобраться, сейчас оставил в подсказке только пароль
    jira_pass = questionary.password(
        "Jira password:",
        default=default.get("jira", "pass", fallback="")
    ).ask()

    config["jira"] = {
        "login": jira_login,
        "pass": jira_pass,
        "url": questionary.text(
            "Jira URL:",
            default=default.get("jira", "url", fallback=jira_url_default)
        ).ask(),
        "days": questionary.text(
            "Days to sync:",
            default=default.get("jira", "days", fallback="30")
        ).ask()
    }

    # Секция [gitlab]
    # Сначала запрашиваем URL
    gitlab_url = questionary.text(
        "GitLab URL:",
        default=default.get("gitlab", "url", fallback="https://gitlab.zebrains.team" if is_zebrains_user else "https://gitlab.zebrains.team")
    ).ask()

    gitlab_token_instruction = f"\n  [Select scopes: api]\n  [Получить токен: {gitlab_url}/-/user_settings/personal_access_tokens]"

    config["gitlab"] = {
        "email": questionary.text(
            "GitLab email:",
            default=default.get("gitlab", "email", fallback=user_email)
        ).ask(),
        "url": gitlab_url,  # Используем сохраненное значение
        "token": questionary.password(
            "GitLab access token:",
            default=default.get("gitlab", "token", fallback=""),
            instruction=gitlab_token_instruction
        ).ask(),
        "days": questionary.text(
            "Days to sync:",
            default=default.get("gitlab", "days", fallback="30")
        ).ask()
    }

    # Сохраняем конфиг
    with open(CONFIG_FILE, "w") as f:
        config.write(f)

    print("\n✅ Конфигурация сохранена в .litconfig")
