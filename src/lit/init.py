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
    jira_url_default = "https://jira.itech-group.ru" if is_zebrains_user else ""

    jira_url = questionary.text(
        "Jira URL:",
        default=default.get("jira", "url", fallback=jira_url_default)
    ).ask()
    is_cloud = ".atlassian.net" in (jira_url or "").lower()

    jira_email_default = (
        default.get("jira", "email", fallback="")
        or default.get("jira", "login", fallback="")
        or user_email
    )

    if is_cloud:
        jira_login = questionary.text(
            "Jira email:",
            default=jira_email_default
        ).ask()
        jira_email = jira_login
        jira_pass = questionary.password(
            "Jira API token:",
            default=default.get("jira", "pass", fallback=""),
            instruction=(
                "\n  [Cloud: basic auth = email + API token]"
                "\n  [Создать токен: https://id.atlassian.com/manage-profile/security/api-tokens]"
            )
        ).ask()
    else:
        jira_login = questionary.text(
            "Jira login:",
            default=default.get("jira", "login", fallback=user_email.split("@")[0] if "@" in user_email else "")
        ).ask()
        jira_email = default.get("jira", "email", fallback="")
        jira_pass = questionary.password(
            "Jira password или PAT:",
            default=default.get("jira", "pass", fallback=""),
            instruction="\n  [Data Center: пароль или personal access token]"
        ).ask()

    config["jira"] = {
        "login": jira_login,
        "email": jira_email,
        "pass": jira_pass,
        "url": jira_url,
        "days": questionary.text(
            "Days to sync:",
            default=default.get("jira", "days", fallback="30")
        ).ask(),
        "api_version": default.get("jira", "api_version", fallback="auto"),
    }

    # Секция [gitlab]
    # Сначала запрашиваем URL
    gitlab_url = questionary.text(
        "GitLab URL:",
        default=default.get("gitlab", "url", fallback="https://gitlab.zebrains.team" if is_zebrains_user else "")
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
