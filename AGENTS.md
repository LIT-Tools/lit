# AGENTS.md

Общайся со мной на Русском языке.

## О проекте
CLI-инструмент `lit` (Logging Integrated Timekeeper) для управления ворклогами с интеграцией Jira и GitLab. Стек: Python 3.9+, uv.

> Источник истины по возможностям, установке и форматам — [`README.md`](./README.md).
> При расхождении прав README, а этот файл обнови под него.

## Быстрый старт
- Установка окружения и зависимостей (dev ставится по умолчанию): `uv sync`
- Запуск тестов с покрытием:
  ```bash
  uv run coverage run -m unittest discover
  uv run coverage report -m
  ```
- HTML-отчёт покрытия: `uv run coverage html` → открыть `htmlcov/index.html`
- Сборка бинарника: `uv run pyinstaller lit.spec`

## Ключевые соглашения
- **Коммиты**: Conventional Commits, инструкция — `.agents/skills/git-commit-convention/SKILL.md`.
- **Ветки**: `master` — стабильная, `dev` — разработка, фичи — `feature/*`.
- **Релизы**: автоматизированы через `release-please`.

## Архитектура (кратко)
- `*.py` — исходники CLI (плоская структура; рефакторинг под `src/lit/` запланирован)
- `test_*.py` — тесты (`unittest` + `coverage`)
- `lit.spec` — конфиг PyInstaller

## Данные и конфигурация
- `~/.lit/.litconfig` — конфиг (`[user]`, `[jira]`, `[gitlab]`), создаётся через `lit init`
- `.litstore` — подготовленные записи
- `.lithistory` — отправленные записи с ID ворклогов
