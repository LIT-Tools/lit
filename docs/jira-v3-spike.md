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

## Write-test на EFESP-281

Использован сложный комментарий:

```text
первая строка
        вторая строка

третья строка: <tag> & "quotes" & 'single'
эмодзи: 🚀
```

### ADF

```text
add_worklog: OK, id = 217800
read back: OK, comment type = PropertyHolder
read back raw comment type: dict
delete: OK
```

ADF прочитан обратно **без искажений**: сохранились пустой
`paragraph`, ведущие пробелы, спецсимволы `< > & " '` и эмодзи.
Пустой `paragraph` (`{"type": "paragraph"}`) Jira принимает.

### Plain string на v3

```text
add_worklog: FAILED
JIRAError status=400: INVALID_INPUT
```

Подтверждено: на v3 `comment` обязан быть ADF. Строка отклоняется.

После теста worklog удалён; в `EFESP-281` осталось 0 worklog'ов.

## Проверка текущей реализации lit

С новым токеном:

| Команда | Результат |
|---|---|
| `lit --help` | `exit=0` |
| `lit -v` | `lit v1.1.0`, `exit=0` |
| `lit status` | `Нет подготовленных записей`, `exit=0` |
| `lit pull --jira` | **`NameError: TARGET_USER`**, `exit=1` |
| `lit push` | работает на v2: worklog `217802` создан и удалён |

То есть текущий push на v2 с plain string пока работает, а pull
сломан ещё до поиска задач. Это подтверждает необходимость шага 6.

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
8. ADF-комментарий принимается `add_worklog` и читается обратно без
   искажений.
9. Plain string на v3 отклоняется с `400 INVALID_INPUT`.
10. Текущий `lit push` на v2 работает, а `lit pull --jira` падает с
    `NameError: TARGET_USER`.

## Что осталось

- Реализовать шаги 2–8 из `REFACTORING.md`.
- После исправления pull проверить `lit pull --jira` на реальном
  инстансе.
- Проверить `lit push` после перехода на v3 и ADF.

## Следующий шаг

Шаг 1 завершён. Переходим к шагу 2 — `src/lit/exceptions.py` и отказ от
`exit()` в интеграциях.
