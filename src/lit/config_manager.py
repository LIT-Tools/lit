"""Чтение конфигурации lit (~/.lit/.litconfig)."""
from configparser import RawConfigParser
from lit.constants import CONFIG_FILE


def load_config(path=None) -> RawConfigParser:
    """Прочитать конфиг с сохранением регистра ключей."""
    cfg = RawConfigParser()
    cfg.optionxform = lambda option: option  # Отключаем авто-преобразование в lowercase
    cfg.read([path or CONFIG_FILE])
    return cfg


def get_user(cfg=None) -> dict:
    """Получить секцию [user]."""
    cfg = cfg or load_config()
    return {
        "email": cfg.get("user", "email", fallback=""),
        "editor": cfg.get("user", "editor", fallback=""),
    }


def get_jira(cfg=None) -> dict:
    """Получить секцию [jira]."""
    cfg = cfg or load_config()
    login = (
        cfg.get("jira", "login", fallback="")
        or cfg.get("jira", "email", fallback="")
    )
    email = cfg.get("jira", "email", fallback="") or login
    api_version = (
        cfg.get("jira", "api_version", fallback="auto").strip().lower()
        or "auto"
    )
    return {
        "login": login,
        "email": email,
        "pass": cfg.get("jira", "pass", fallback=""),
        "url": cfg.get("jira", "url", fallback=""),
        "days": cfg.getint("jira", "days", fallback=30),
        "api_version": api_version,
    }


def get_gitlab(cfg=None) -> dict:
    """Получить секцию [gitlab]."""
    cfg = cfg or load_config()
    email = cfg.get("gitlab", "email", fallback="") or cfg.get("gitlab", "login", fallback="")
    return {
        "email": email,
        "url": cfg.get("gitlab", "url", fallback=""),
        "token": cfg.get("gitlab", "token", fallback=""),
        "days": cfg.getint("gitlab", "days", fallback=30),
    }


# Для совместимости с тестами, мокающими import_gitlab.load_config()
