# Spike: Jira Cloud REST API v3

Дата: 2026-10-23
Ветка: `feature/jira-v3`
Скрипт: `scripts/jira_v3_probe.py`

## Конфигурация

| Параметр | Значение |
|---|---|
| URL | `https://dev-krd.atlassian.net` |
| login / email | `s.kushnarev@spider.ru` |
| pass | `ATAT...071D` (API token, замаскирован) |
| days | 30 |

## История запусков

1. Первый запуск — `401 AUTHENTICATED_FAILED`: токен был просрочен.
2. После обновления токена — авторизация успешна.

## Результат авторизации

```text
deploymentType: Cloud
_is_cloud: True
server_info.version: 1001.0.0-SNAPSHOT
current_user: 712020:6e48eeea-4616-4b4f-8fb0-b8dc86835d49
```

`current_user()` возвращает `accountId`, а не email. Это нормально для
Jira Cloud.

## Получение задач

Успешно получены задачи по обоим JQL:

```text
assignee = currentUser() ORDER BY updated DESC
found: 5

worklogAuthor = currentUser() AND worklogDate >= -30d ORDER BY updated DESC
found: 4
```

Примеры:

- `EFESF-12` — Архитектурное сопровождение Fleet Tools;
- `EFESC-459` — Падение джобы sync-swe-upl-products;
- `EFESA-684` — Смена домена почтовых адресов пользователей.

## Типы полей

### description

Для задачи `EFESC-459`:

```text
description type: PropertyHolder
raw fields.description type: dict
```

Сырой ответ API — **ADF**:

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "codeBlock",
      "attrs": {"localId": "...", "wrap": true},
      "content": [{"type": "text", "text": "..."}]
    }
  ]
}
```

Важно: если `description` не указан в `fields` запроса поиска, поле
приходит как `None`, даже если JQL `description is not EMPTY` его нашёл.
Для чтения description его нужно явно запрашивать.

### worklog comment

Для задачи `EFESA-684`:

```text
worklog comment type: PropertyHolder
raw worklog comment type: dict
```

Сырой ответ API — **ADF**:

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "paragraph",
      "content": [{"type": "text", "text": "Анализ почтовых адресов в БД"}],
      "attrs": {"localId": "7764743687a5"}
    }
  ]
}
```

Вывод: на v3 `comment` в worklog — действительно ADF, а
`PropertyHolder` — это обёртка библиотеки, реальные данные лежат в
`.raw`.

## Пагинация

Подтверждено: `startAt` на Cloud ломается.

```text
startAt=1 -> JIRAError:
The `search` API is deprecated in Jira Cloud.
Use `enhanced_search_issues` method instead.
```

`enhanced_search_issues()` работает:

```text
enhanced_search_issues -> OK, issues: 2
```

Следовательно, текущий цикл в `src/lit/integrations/jira.py:83-105`
нужно заменить на `enhanced_search_issues` / `nextPageToken` или
`maxResults=False`.

## JQL

`currentUser()` работает и для `assignee`, и для `worklogAuthor`.
Это позволяет убрать неопределённый `TARGET_USER` из `jira.py`.

## Что подтверждено

1. Инстанс — Jira Cloud.
2. Клиент с `rest_api_version="3"` работает.
3. Basic auth — email + API token.
4. Задачи по `assignee = currentUser()` и `worklogAuthor = currentUser()`
   получаются.
5. `description` и `comment` в v3 — ADF (`dict`).
6. `startAt`-пагинация на Cloud не работает.
7. `enhanced_search_issues` доступен и возвращает результаты.

## Что ещё нужно проверить

- Приём ADF в `add_worklog` на v3 (ожидается `201`).
- Поведение v3 при plain string в `comment` (ожидается `400`).
- Создание/удаление тестового worklog через `--write-test`.

Для этого нужна безопасная задача (sandbox), например `TEST-123`.
Write-test создаёт worklog на 1 минуту и сразу удаляет его.

## Следующий шаг

1. Указать безопасную задачу для `--write-test`.
2. Проверить ADF и plain string.
3. Перейти к шагам 2–8 из `REFACTORING.md`.
