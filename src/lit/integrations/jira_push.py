from __future__ import annotations

from datetime import datetime
import os

from jira import JIRA
from jira.exceptions import JIRAError
from tzlocal import get_localzone

from lit.constants import LIT_DIR
from lit.exceptions import JiraIntegrationError
from lit.integrations.adf import plain_text_to_adf
from lit.integrations.jira_client import (
    build_jira,
    client_api_version,
    format_jira_error,
)

os.makedirs(LIT_DIR, exist_ok=True)


def jira_connect() -> JIRA:
    """Создать клиент Jira и проверить подключение."""
    jira = build_jira()

    try:
        print(f"Успешное подключение к Jira {jira.server_info()['version']}")
        print(f"Авторизованы как: {jira.current_user()}")
    except JIRAError as e:
        raise JiraIntegrationError(format_jira_error(e)) from e
    except Exception as e:
        raise JiraIntegrationError(
            f"Ошибка проверки подключения к Jira: {e}"
        ) from e

    return jira


def _format_worklog_error(exc: JIRAError) -> str:
    """Понятное сообщение об ошибке именно добавления ворклога."""
    status = getattr(exc, "status_code", None)
    text = (getattr(exc, "text", None) or str(exc)).strip()
    if status == 401:
        return format_jira_error(exc)
    if status in (400, 404):
        return f"Jira отклонила ворклог ({status}): {text}"
    return f"Ошибка Jira при добавлении ворклога ({status}): {text}"


def add_worklog(
    jira: JIRA,
    issue: str,
    time_spent: str,
    comment: str,
    day: str,
    time: str,
) -> str:
    """Добавить ворклог и вернуть его ID.

    В Jira Cloud (REST API v3) комментарий обязан быть ADF-документом,
    в Data Center (v2) — обычной строкой. ``Worklog`` нормализуется
    к строковому ID, чтобы вызывающий код не зависел от типа ответа.
    """
    start_time = datetime.strptime(
        f"{day} {time}", "%d.%m.%Y %H:%M"
    ).replace(tzinfo=get_localzone())

    payload = {"timeSpent": time_spent, "started": start_time}
    if comment:
        if client_api_version(jira) == "3":
            payload["comment"] = plain_text_to_adf(comment)
        else:
            payload["comment"] = comment

    try:
        worklog = jira.add_worklog(issue, **payload)
    except JIRAError as e:
        raise JiraIntegrationError(_format_worklog_error(e)) from e
    except Exception as e:
        raise JiraIntegrationError(
            f"Ошибка добавления ворклога: {e}"
        ) from e

    if worklog is None:
        raise JiraIntegrationError("Jira не вернула ID ворклога")
    return str(worklog)
