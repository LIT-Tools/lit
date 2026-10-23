"""Исключения приложения lit."""
from __future__ import annotations


class LitError(Exception):
    """Базовая ошибка приложения."""


class JiraIntegrationError(LitError):
    """Ошибка интеграции с Jira."""


class GitLabIntegrationError(LitError):
    """Ошибка интеграции с GitLab."""


class ConfigError(LitError):
    """Ошибка конфигурации."""
