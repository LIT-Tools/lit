"""Чтение конфигурации lit (~/.lit/.litconfig)."""
from configparser import RawConfigParser
from constants import CONFIG_FILE


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
        "login": cfg.get("user", "login", fallback=""),
        "email": cfg.get("user", "email", fallback=""),
        "editor": cfg.get("user", "editor", fallback=""),
    }


def get_jira(cfg=None) -> dict:
    """Получить секцию [jira]."""
    cfg = cfg or load_config()
    return {
        "login": cfg.get("jira", "login", fallback=""),
        "email": cfg.get("jira", "email", fallback=""),
        "pass": cfg.get("jira", "pass", fallback=""),
        "url": cfg.get("jira", "url", fallback=""),
        "days": cfg.getint("jira", "days", fallback=30),
    }


def get_gitlab(cfg=None) -> dict:
    """Получить секцию [gitlab]."""
    cfg = cfg or load_config()
    return {
        "login": cfg.get("gitlab", "login", fallback=""),
        "email": cfg.get("gitlab", "email", fallback=""),
        "url": cfg.get("gitlab", "url", fallback=""),
        "token": cfg.get("gitlab", "token", fallback=""),
        "days": cfg.getint("gitlab", "days", fallback=30),
    }


# Для совместимости с тестами, мокающими import_gitlab.load_config()
