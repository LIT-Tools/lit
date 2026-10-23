# Spike: Jira Cloud REST API v3

Дата: 2026-10-23
Ветка: `feature/jira-v3`
Скрипт: `scripts/jira_v3_probe.py`

## Конфигурация

| Параметр | Значение |
|---|---|
| URL | `https://dev-krd.atlassian.net` |
| login / email | `s.kushnarev@spider.ru` |
| pass | `ATAT...76F6` (192 символа, без пробелов и кавычек) |
| days | 30 |

Секреты в отчёте замаскированы.

## Результат авторизации

**Авторизация не прошла.**

```text
GET /rest/api/3/myself
HTTP 401
X-Seraph-Loginreason: AUTHENTICATED_FAILED
Body: "Client must be authenticated to access this resource."
```

Проверено:

- `basic_auth` с `login` и с `email` — оба варианта дают `401`;
- `Authorization: Bearer <token>` — `403 Failed to parse Connect Session Auth Token`
  (для Cloud API token это не тот способ);
- токен не обрезан: длина 192, префикс `ATATT3xF`, суффикс `76F6`,
  пробелов/кавычек/многоточий нет;
- `login` и `email` в конфиге совпадают;
- анонимный запрос к `/rest/api/3/myself` тоже даёт `401`, а
  `/rest/api/3/project` анонимно возвращает `200 []`;
- `search/jql` анонимно возвращает `200 {"issues":[],"isLast":true}`.

Вывод: часть endpoint'ов доступна анонимно и возвращает пустой результат,
поэтому «пустой список задач» **не является** признаком успешной
авторизации. Признак успеха — `current_user()` и непустой `/myself`.

## Что подтверждено

1. Инстанс — **Jira Cloud**:
   - `deploymentType: Cloud`;
   - `_is_cloud: True`;
   - `server_info()` доступен анонимно: версия `1001.0.0-SNAPSHOT`.
2. Клиент с `options={"rest_api_version": "3"}` создаётся, версия
   подхватывается (`rest_api_version: 3`).
3. **Пагинация `startAt` на Cloud ломается**:

   ```text
   startAt=1 -> JIRAError:
   The `search` API is deprecated in Jira Cloud.
   Use `enhanced_search_issues` method instead.
   ```

   Это подтверждает, что текущий цикл в
   `src/lit/integrations/jira.py:83-105` непригоден для Cloud.
4. `enhanced_search_issues()` доступен и возвращает `ResultList`
   (при отсутствии auth — пустой).
5. `assignee = currentUser()` и
   `worklogAuthor = currentUser() AND worklogDate >= -30d` синтаксически
   принимаются Cloud (возвращают пустой список без auth).

## Что ещё не подтверждено

Из-за `401` не удалось проверить:

- тип `description` у реальной задачи (`dict`/ADF или `str`);
- тип `comment` у worklog;
- поведение v3 при plain string в `comment`;
- приём ADF-комментария;
- работу `--write-test` (создание/удаление worklog).

Эти пункты нужно проверить после обновления токена.

## Что нужно обновить в кредах

Наиболее вероятные причины `AUTHENTICATED_FAILED`:

1. **Токен истёк или был отозван** (например, после смены пароля или
   ручного revoke).
2. **Токен выпущен для другого Atlassian-аккаунта**, а не для
   `s.kushnarev@spider.ru`.
3. **В организации отключён доступ по API-токенам** (политика
   администратора Atlassian).
4. **Email в конфиге не совпадает** с email аккаунта, для которого
   выпущен токен.

Что сделать:

1. Открыть <https://id.atlassian.com/manage-profile/security/api-tokens>.
2. Убедиться, что вход выполнен под аккаунтом, у которого есть доступ к
   `dev-krd.atlassian.net`.
3. Создать новый API token (или проверить срок действия текущего).
4. Обновить в `~/.lit/.litconfig`:

   ```ini
   [jira]
   login = <email аккаунта Atlassian>
   email = <тот же email>
   pass = <полный новый API token>
   url = https://dev-krd.atlassian.net
   days = 30
   ```

   Токен вставлять целиком, без кавычек, пробелов и переносов строк.

5. Проверить:

   ```bash
   uv run python scripts/jira_v3_probe.py
   ```

   Признак успеха — `current_user:` без `FAILED` и непустой список задач.

## Следующий шаг

После обновления токена:

1. Повторить read-only probe.
2. Зафиксировать типы `description` и `comment`.
3. Выполнить `--write-test` на безопасной тестовой задаче.
4. После этого переходить к шагам 2–8 из `REFACTORING.md`.
