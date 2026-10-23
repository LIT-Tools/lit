"""Единый клиент Jira с выбором версии REST API.

Jira Cloud работает через REST API v3, Jira Data Center — через v2.
Версию можно задать явно (``api_version = 2`` / ``3``) или доверить
автоопределению (``auto``).
"""
from __future__ import annotations

from typing import Optional

from jira import JIRA
from jira.exceptions import JIRAError

from lit.config_manager import get_jira
from lit.exceptions import ConfigError, JiraIntegrationError

DEFAULT_FIELDS = "key,summary,status,assignee"


def _configured_version(cfg: dict) -> str:
    """Вернуть значение ``api_version`` из конфига или ``auto``."""
    raw = str(cfg.get("api_version", "auto")).strip().lower()
    if raw in ("", "auto"):
        return "auto"
    if raw in ("2", "3"):
        return raw
    raise ConfigError(
        f"Неверный api_version в конфиге: {raw!r}. Ожидается auto, 2 или 3."
    )


def resolve_api_version(
    cfg: Optional[dict] = None,
    jira: Optional[JIRA] = None,
) -> str:
    """Определить версию API по конфигу и/или уже созданному клиенту.

    Если версия задана явно, возвращается она. Если ``auto`` и клиент
    передан, версия выводится из признака Cloud. Без клиента ``auto``
    остаётся ``auto`` — решение принимает :func:`build_jira`.
    """
    cfg = cfg if cfg is not None else get_jira()
    version = _configured_version(cfg)
    if version != "auto":
        return version
    if jira is None:
        return "auto"
    return "3" if getattr(jira, "_is_cloud", False) else "2"


def _make_client(cfg: dict, api_version: str) -> JIRA:
    """Создать ``JIRA`` с указанной версией REST API."""
    login = cfg.get("login") or cfg.get("email") or ""
    url = cfg["url"]
    return JIRA(
        server=url,
        basic_auth=(login, cfg["pass"]),
        options={
            "server": url,
            "rest_api_version": api_version,
            "verify": True,
        },
        timeout=20,
    )


def _create_client(cfg: dict, api_version: str) -> JIRA:
    """Создать клиент и обернуть ошибки в :class:`JiraIntegrationError`."""
    try:
        return _make_client(cfg, api_version)
    except JIRAError as exc:
        raise JiraIntegrationError(format_jira_error(exc)) from exc
    except Exception as exc:
        raise JiraIntegrationError(
            f"Ошибка подключения к Jira: {exc}"
        ) from exc


def build_jira(cfg: Optional[dict] = None) -> JIRA:
    """Создать клиент Jira с подходящей версией REST API.

    В режиме ``auto`` сначала пробуем v3: она работает на Cloud. Если
    инстанс оказался Data Center, клиент пересоздаётся на v2. Если v3
    недоступна (400/404), также откатываемся на v2.
    """
    cfg = cfg if cfg is not None else get_jira()
    version = _configured_version(cfg)
    if version != "auto":
        return _create_client(cfg, version)

    try:
        client = _make_client(cfg, "3")
    except JIRAError as exc:
        if getattr(exc, "status_code", None) in (400, 404):
            return _create_client(cfg, "2")
        raise JiraIntegrationError(format_jira_error(exc)) from exc
    except Exception as exc:
        raise JiraIntegrationError(
            f"Ошибка подключения к Jira: {exc}"
        ) from exc

    if getattr(client, "_is_cloud", False):
        return client

    # Data Center: клиент v3 не подходит, пересоздаём на v2.
    close = getattr(client, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass
    return _create_client(cfg, "2")


def search_all_issues(
    jira: JIRA,
    jql: str,
    fields: str = DEFAULT_FIELDS,
) -> list:
    """Получить все задачи по JQL без ручного листания страниц.

    На Cloud используется ``enhanced_search_issues`` (nextPageToken),
    на Data Center — ``search_issues``. В обоих случаях
    ``maxResults=False`` означает «забрать все страницы».
    """
    try:
        if getattr(jira, "_is_cloud", False):
            issues = jira.enhanced_search_issues(
                jql, maxResults=False, fields=fields
            )
        else:
            issues = jira.search_issues(
                jql, maxResults=False, fields=fields
            )
    except JIRAError as exc:
        raise JiraIntegrationError(format_jira_error(exc)) from exc
    return list(issues or [])


def format_jira_error(exc: BaseException) -> str:
    """Человекочитаемое сообщение об ошибке Jira."""
    if not isinstance(exc, JIRAError):
        return f"Ошибка интеграции с Jira: {exc}"

    status = getattr(exc, "status_code", None)
    text = getattr(exc, "text", None) or str(exc)
    text = str(text).strip()
    if len(text) > 500:
        text = text[:500] + "…"

    if status == 401:
        return (
            "Ошибка авторизации Jira (401). "
            "Проверьте email/login и API token в ~/.lit/.litconfig."
        )
    if status == 403:
        return f"Нет прав доступа к Jira (403): {text}"
    if status == 404:
        return (
            "Jira endpoint не найден (404). "
            "Проверьте url и api_version в ~/.lit/.litconfig."
        )
    return f"Ошибка Jira ({status}): {text}"
