#!/usr/bin/env python
"""Spike: проверка Jira Cloud REST API v3.

Одноразовый диагностический скрипт. По умолчанию работает только на
чтение. Запись (создание/удаление тестового worklog) включается явно
через ``--write-test ISSUE-KEY``.

Запуск:
    uv run python scripts/jira_v3_probe.py
    uv run python scripts/jira_v3_probe.py --write-test TEST-123

Секреты в вывод не попадают.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

from jira import JIRA
from jira.exceptions import JIRAError

from lit.config_manager import get_jira

JQL_ASSIGNEE = "assignee = currentUser() ORDER BY updated DESC"
JQL_WORKLOG = "worklogAuthor = currentUser() AND worklogDate >= -30d ORDER BY updated DESC"


def mask(value: str) -> str:
    """Скрыть секрет, оставив только края."""
    if not value:
        return "<empty>"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def short(value: Any, limit: int = 600) -> str:
    """Короткое представление значения для лога."""
    if value is None:
        return "<None>"
    try:
        text = json.dumps(value, ensure_ascii=False, indent=2)
    except TypeError:
        text = repr(value)
    if len(text) > limit:
        return text[:limit] + "…"
    return text


def explain(exc: BaseException) -> str:
    """Человекочитаемое объяснение ошибки Jira."""
    if isinstance(exc, JIRAError):
        status = getattr(exc, "status_code", None)
        text = getattr(exc, "text", None) or str(exc)
        hints = {
            400: "Проверьте формат запроса. Для v3 comment должен быть ADF.",
            401: (
                "Не прошла аутентификация. Для Jira Cloud basic_auth = "
                "(email, API token). Проверьте login/email и pass в [jira]."
            ),
            403: (
                "Пользователь аутентифицирован, но нет прав. "
                "Проверьте доступ к проекту/задаче и scope токена."
            ),
            404: "URL или endpoint не найден. Проверьте url и rest_api_version.",
            429: "Слишком много запросов. Подождите и повторите.",
        }
        hint = hints.get(status, "Проверьте URL, креды и права доступа.")
        return f"JIRAError status={status}: {str(text)[:1000]}\n  Подсказка: {hint}"
    return f"{type(exc).__name__}: {exc}"


def make_client(cfg: dict, version: str) -> JIRA:
    """Создать клиент Jira с указанной версией REST API."""
    login = cfg.get("login") or cfg.get("email") or ""
    return JIRA(
        server=cfg["url"],
        basic_auth=(login, cfg["pass"]),
        options={
            "server": cfg["url"],
            "rest_api_version": version,
            "verify": True,
        },
        timeout=20,
    )


def print_client_info(label: str, jira: JIRA, cfg: dict) -> bool:
    """Печать сведений о клиенте и подключении.

    Возвращает True, если удалось получить текущего пользователя.
    """
    print(f"\n=== {label} ===")
    print("server:", cfg.get("url"))
    print("login/email:", cfg.get("login") or cfg.get("email"))
    print("pass:", mask(cfg.get("pass", "")))
    print("rest_api_version:", jira._options.get("rest_api_version"))
    print("deploymentType:", getattr(jira, "deploymentType", None))
    print("_is_cloud:", getattr(jira, "_is_cloud", None))

    try:
        info = jira.server_info()
    except Exception as exc:  # noqa: BLE001 - диагностический скрипт
        print("server_info: FAILED")
        print(explain(exc))
    else:
        print("server_info.version:", info.get("version"))
        print("server_info.deploymentType:", info.get("deploymentType"))

    try:
        me = jira.current_user()
    except Exception as exc:  # noqa: BLE001
        print("current_user: FAILED")
        print(explain(exc))
        print("ВНИМАНИЕ: без авторизации результаты поиска не показательны.")
        return False
    else:
        print("current_user:", me)
        return True


def search(jira: JIRA, jql: str, limit: int = 5, auth_ok: bool = True) -> list:
    """Поиск задач и печать краткой информации."""
    print(f"\nJQL: {jql}")
    try:
        issues = jira.search_issues(
            jql,
            maxResults=limit,
            fields="key,summary,status,assignee,updated",
        )
    except Exception as exc:  # noqa: BLE001
        print("search: FAILED")
        print(explain(exc))
        return []

    suffix = "" if auth_ok else " (без авторизации — не показательны)"
    print(f"found: {len(issues)} (limit {limit}){suffix}")
    for issue in issues:
        fields = issue.fields
        status = getattr(getattr(fields, "status", None), "name", None)
        assignee = getattr(getattr(fields, "assignee", None), "displayName", None)
        print(f"  {issue.key}: {fields.summary} [status={status}, assignee={assignee}]")
    return list(issues)


def probe_issue_details(jira: JIRA, issue) -> None:
    """Проверить типы description и worklog comment."""
    print(f"\n=== Детали {issue.key} ===")
    description = getattr(issue.fields, "description", None)
    print("description type:", type(description).__name__)
    print("description sample:", short(description))

    try:
        worklogs = jira.worklogs(issue.key)
    except Exception as exc:  # noqa: BLE001
        print("worklogs: FAILED")
        print(explain(exc))
        return

    print("worklogs:", len(worklogs))
    if worklogs:
        comment = getattr(worklogs[0], "comment", None)
        print("worklog comment type:", type(comment).__name__)
        print("worklog comment sample:", short(comment))


def probe_pagination(jira: JIRA, jql: str) -> None:
    """Проверить, ломается ли startAt на Cloud и работает ли enhanced search."""
    print("\n=== Пагинация ===")
    try:
        jira.search_issues(jql, startAt=1, maxResults=1, fields="key")
    except JIRAError as exc:
        print("startAt=1 -> JIRAError (ожидаемо для Cloud):")
        print(explain(exc))
    except Exception as exc:  # noqa: BLE001
        print("startAt=1 -> unexpected:")
        print(explain(exc))
    else:
        print("startAt=1 -> OK (для Cloud неожидаемо)")

    if getattr(jira, "_is_cloud", False):
        try:
            page = jira.enhanced_search_issues(jql, maxResults=2, fields="key,summary")
        except Exception as exc:  # noqa: BLE001
            print("enhanced_search_issues -> FAILED")
            print(explain(exc))
        else:
            print("enhanced_search_issues -> OK, issues:", len(page))


def plain_text_to_adf(text: str) -> dict:
    """Минимальный ADF для spike (не production-код)."""
    if not text:
        return {"type": "doc", "version": 1, "content": []}
    content = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.strip():
            content.append(
                {"type": "paragraph", "content": [{"type": "text", "text": line}]}
            )
        else:
            content.append({"type": "paragraph"})
    return {"type": "doc", "version": 1, "content": content}


def write_test(jira: JIRA, issue_key: str, use_adf: bool) -> None:
    """Создать, прочитать и удалить тестовый worklog."""
    label = "ADF" if use_adf else "plain string"
    print(f"\n=== Write test: {label} -> {issue_key} ===")
    comment: Any = plain_text_to_adf("lit v3 probe") if use_adf else "lit v3 probe"

    try:
        worklog = jira.add_worklog(
            issue_key,
            timeSpent="1m",
            comment=comment,
            started=datetime.now(timezone.utc),
        )
    except Exception as exc:  # noqa: BLE001
        print("add_worklog: FAILED")
        print(explain(exc))
        return

    worklog_id = getattr(worklog, "id", None) or str(worklog)
    print("add_worklog: OK, id =", worklog_id)

    try:
        fetched = jira.worklog(issue_key, worklog_id)
    except Exception as exc:  # noqa: BLE001
        print("read back: FAILED")
        print(explain(exc))
    else:
        comment_type = type(getattr(fetched, "comment", None)).__name__
        print("read back: OK, comment type =", comment_type)

    try:
        worklog.delete()
    except Exception as exc:  # noqa: BLE001
        print("delete: FAILED — удалите worklog вручную:", worklog_id)
        print(explain(exc))
    else:
        print("delete: OK")


def main() -> int:
    parser = argparse.ArgumentParser(description="Spike: Jira Cloud REST API v3")
    parser.add_argument(
        "--write-test",
        metavar="ISSUE-KEY",
        help="создать и удалить тестовый worklog в указанной задаче",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="сколько задач показывать (default: 5)",
    )
    args = parser.parse_args()

    cfg = get_jira()
    missing = [key for key in ("url", "pass") if not cfg.get(key)]
    if not (cfg.get("login") or cfg.get("email")):
        missing.append("login/email")
    if missing:
        print("Не хватает полей в [jira]:", ", ".join(missing))
        print("Запустите `lit init` или добавьте их в ~/.lit/.litconfig.")
        return 2

    print("Конфиг:", cfg.get("url"))
    print("login/email:", cfg.get("login") or cfg.get("email"))
    print("pass:", mask(cfg.get("pass", "")))
    print("days:", cfg.get("days"))

    try:
        jira_v3 = make_client(cfg, "3")
    except Exception as exc:  # noqa: BLE001
        print("\nНе удалось создать клиент v3.")
        print(explain(exc))
        return 1

    auth_ok = print_client_info("Jira v3", jira_v3, cfg)

    issues = search(jira_v3, JQL_ASSIGNEE, args.limit, auth_ok=auth_ok)
    search(jira_v3, JQL_WORKLOG, args.limit, auth_ok=auth_ok)

    if issues:
        probe_issue_details(jira_v3, issues[0])
    elif auth_ok:
        print("\nНет задач для проверки description/worklog.")
    else:
        print("\nПроверка description/worklog пропущена: нет авторизации.")

    probe_pagination(jira_v3, JQL_ASSIGNEE)

    print("\n=== Сравнение с v2 ===")
    try:
        jira_v2 = make_client(cfg, "2")
    except Exception as exc:  # noqa: BLE001
        print("v2 client: FAILED")
        print(explain(exc))
    else:
        auth_ok_v2 = print_client_info("Jira v2", jira_v2, cfg)
        search(jira_v2, JQL_ASSIGNEE, min(args.limit, 3), auth_ok=auth_ok_v2)

    if args.write_test:
        if not auth_ok:
            print("\nwrite-test пропущен: нет авторизации.")
            return 1
        write_test(jira_v3, args.write_test, use_adf=True)
        write_test(jira_v3, args.write_test, use_adf=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
