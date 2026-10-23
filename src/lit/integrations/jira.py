from __future__ import annotations

import json
from datetime import datetime, timedelta

from jira.exceptions import JIRAError

from lit.config_manager import get_jira
from lit.constants import TASKS_FILE
from lit.exceptions import JiraIntegrationError
from lit.integrations.jira_client import (
    build_jira,
    format_jira_error,
    search_all_issues,
)


def save_commits(data: dict) -> None:
    """Сохранить задачи в файл с атомарной записью."""
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving commits: {e}")


def _resolve_user(config: dict, jira) -> tuple[str, str]:
    """Вернуть JQL-значение пользователя и его отображаемое имя.

    На Cloud и DC штатно работает ``currentUser()``. Если клиент не
    может определить пользователя, откатываемся на email/login из
    конфига.
    """
    try:
        user = jira.current_user()
    except Exception as e:
        print(f"Не удалось определить текущего пользователя Jira: {e}")
    else:
        if user:
            return "currentUser()", user

    fallback = config.get("email") or config.get("login")
    if not fallback:
        raise JiraIntegrationError(
            "Не удалось определить пользователя Jira: currentUser() недоступен, "
            "а email/login в конфиге не заданы."
        )
    print(f"Использую пользователя из конфига: {fallback}")
    return json.dumps(fallback), fallback


def load_tasks_from_jira() -> None:
    config = get_jira()
    days = config["days"]

    jira = build_jira(config)

    try:
        print(f"Успешное подключение к Jira {jira.server_info()['version']}")
    except JIRAError as e:
        raise JiraIntegrationError(format_jira_error(e)) from e
    except Exception as e:
        raise JiraIntegrationError(
            f"Ошибка проверки подключения к Jira: {e}"
        ) from e

    user_clause, user = _resolve_user(config, jira)
    print(f"Авторизованы как: {user}")

    today = datetime.today()
    start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")

    jql_assignee = f'assignee = {user_clause} AND updated >= "{start_date}"'
    jql_worklog = (
        f'worklogAuthor = {user_clause} AND worklogDate >= "{start_date}"'
    )

    print("Поиск задач...", end="", flush=True)
    assignee_issues = search_all_issues(jira, jql_assignee)
    print(f"\rНайдено задач: {len(assignee_issues)}")

    print("Поиск задач по ворклогам...", end="", flush=True)
    worklog_issues = search_all_issues(jira, jql_worklog)
    print(f"\rВ задач логал: {len(worklog_issues)}" + " " * 30)

    all_issues = assignee_issues + worklog_issues
    unique_issues = list({issue.key: issue for issue in all_issues}.values())
    print(f"Всего уникальных задач: {len(unique_issues)}")

    tasks = {issue.key: issue.fields.summary for issue in unique_issues}
    save_commits(tasks)
