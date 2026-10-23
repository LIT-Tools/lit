# Jira REST API v3: план перехода и чек-лист

> Статус: шаг 1 (spike) завершён. ADF принимается, plain string на v3
> отклоняется; текущий `lit pull` падает с `NameError`, `lit push` на v2
> работает.
> Результаты: [`docs/jira-v3-spike.md`](./docs/jira-v3-spike.md).
> Базовая точка: `dev` / `1b30085`; 48 тестов, покрытие 72%.
> Источник истины по командам — [`README.md`](./README.md).

## 1. Контекст

`lit` работает с Jira Cloud (`https://dev-krd.atlassian.net`) через
библиотеку `jira 3.10.5`. Сейчас в коде жёстко задан
`rest_api_version = "2"`.

В Jira Cloud REST API v3:

- `comment` в worklog — **ADF** (Atlassian Document Format), JSON-дерево,
  а не plain text;
- поиск задач — `/rest/api/3/search/jql`, пагинация через
  `nextPageToken`;
- basic auth — **email + API token**, а не логин + пароль.

Библиотека `jira` умеет `options={"rest_api_version": "3"}`, но:

- **не конвертирует** plain text в ADF;
- на Cloud автоматически переключает `search_issues()` на
  `enhanced_search_issues()`, но только при `startAt == 0`;
- при `startAt != 0` на Cloud бросает `JIRAError`
  («The `search` API is deprecated…»).

`lit` использует только четыре возможности Jira:

1. `server_info()` / `current_user()` — проверка подключения;
2. `search_issues()` — `lit pull --jira`;
3. `add_worklog()` — `lit push`;
4. `worklogs()` — только для диагностики, в бизнес-логике не используется.

`description` задач и чтение комментариев в `lit` не используются,
поэтому ADF для `description` в этом цикле **не нужен**.

## 2. Что уже известно (проверено локально)

- Инстанс — **Jira Cloud**: `https://dev-krd.atlassian.net`.
  `jira._is_cloud == True`.
- Baseline: **48 тестов OK**, `TOTAL 72%`.
  `src/lit/integrations/jira.py` — 15%,
  `src/lit/integrations/jira_push.py` — 54%.
- `lit pull --jira` уже сломан: в `src/lit/integrations/jira.py:80-81`
  используется неопределённый `TARGET_USER` → `NameError`.
- Пагинация в `jira.py:83-105` построена на `startAt` и на Cloud
  ломается после первой страницы.
- `jira.add_worklog()` возвращает `Worklog`, а не `str`.
  В `jira_push.py:50` это маскируется тем, что `str(Worklog)` возвращает
  `id`, но проверка `if not id` и типы некорректны.
- В библиотеке `jira` нет хелперов для ADF.
- `src/lit/cli.py` отсутствует: CLI находится в `src/lit/__init__.py`
  (`process_arguments`, `main`).
- `docs/refactoring-log.md`, на который ссылался старый план, отсутствует.

## 3. Цели и не-цели

### Цели

1. Прототип, подтверждающий поведение Jira Cloud v3 на реальном
   инстансе: auth, поиск, типы полей, пагинация, ADF.
2. Единый клиент Jira с выбором версии API (`auto` / `2` / `3`).
3. ADF для `comment` в worklog при v3.
4. Починить `lit pull --jira`: `TARGET_USER`, пагинация, ошибки.
5. Ошибки через исключения, без `exit()` в интеграциях.
6. Тесты на все изменённые пути; не снизить покрытие.

### Не-цели

- ADF для `description` задач;
- чтение и рендер ADF из Jira;
- перенос CLI в отдельный `cli.py`;
- `WorklogEntry` dataclass;
- GitLab;
- auto-update.

## 4. Главные правила

1. **Spike ≠ TDD.** Шаг 1 — разведка. Production-код не трогаем.
   Результат — знание, а не код, который останется в проекте.
2. **TDD после spike.** Шаги 2–8: сначала красный тест на подтверждённое
   поведение, потом минимальная реализация, потом рефактор.
3. **Атомарность.** Один шаг — один коммит. Conventional Commits.
4. **Откат.** Если после 3 точечных правок красное —
   `git checkout . && git clean -fd`, следующая попытка с чистого листа.
5. **Секреты.** Токены и пароли не попадают в логи, отчёты и коммиты.

## 5. Baseline

```bash
git status
git branch --show-current
git log --oneline -3
uv sync
uv run coverage run -m unittest discover
uv run coverage report -m
```

Ожидаемо:

- ветка `feature/jira-v3`;
- дерево чистое;
- `Ran 48 tests`, `OK`;
- `TOTAL` не ниже 72%;
- `jira.py` и `jira_push.py` — основные точки роста покрытия.

Smoke:

```bash
uv run lit --help; echo "exit=$?"
uv run lit -v; echo "exit=$?"
uv run lit status; echo "exit=$?"
```

## 6. Чек-лист

- [x] Шаг 0: Baseline
- [x] Шаг 1: Spike-прототип Jira v3 — завершён (ADF OK, string → 400)
- [ ] Шаг 2: `exceptions.py` + отказ от `exit()`
- [ ] Шаг 3: `plain_text_to_adf()`
- [ ] Шаг 4: `jira_client.py` — единый клиент и выбор версии API
- [ ] Шаг 5: Push — ADF для v3, нормализация `Worklog`
- [ ] Шаг 6: Pull — `currentUser()` и пагинация Cloud
- [ ] Шаг 7: Конфиг, `init`, CLI-граница, документация
- [ ] Шаг 8: Сценарии ошибок + реальный smoke

## 7. Подробные шаги

### Шаг 0: Baseline

- **Цель**: зафиксировать зелёную стартовую точку и хэш для отката.
- **Команды**: см. раздел 5.
- **Признак успеха**: 48 OK, smoke `exit=0`, дерево чистое.
- **Коммит**: не нужен.

---

### Шаг 1: Spike-прототип Jira v3

**Цель**: узнать, как реально ведёт себя Jira Cloud и библиотека `jira`
с `rest_api_version="3"` на вашем инстансе. **Код в `src/` не трогаем.**

#### 1.1. Скрипт `scripts/jira_v3_probe.py`

Скрипт одноразовый, но с двумя режимами:

- **read-only (по умолчанию)** — только чтение:
  - создаёт клиент v3 с `basic_auth=(login/email, pass)`;
  - печатает `rest_api_version`, `deploymentType`, `_is_cloud`,
    `server_info()`, `current_user()` (секреты маскируются);
  - ищет задачи по JQL:
    - `assignee = currentUser() ORDER BY updated DESC`;
    - `worklogAuthor = currentUser() AND worklogDate >= -30d`;
  - печатает ключ, summary, статус, исполнителя;
  - печатает тип `description` у первой задачи;
  - печатает тип `comment` у первого worklog;
  - проверяет пагинацию: `search_issues(..., startAt=1)` — на Cloud
    ожидается `JIRAError`;
  - проверяет `enhanced_search_issues()` на Cloud;
  - создаёт клиент v2 для сравнения.
- **`--write-test ISSUE-KEY`** — только по явному указанию безопасной
  задачи:
  - добавляет worklog на 1 минуту с ADF-комментарием;
  - читает его обратно, проверяет тип `comment`;
  - удаляет worklog;
  - отдельно пробует plain string на v3 (ожидается `400`);
  - если string-worklog всё же создался — удаляет.

#### 1.2. Запуск

```bash
uv run python scripts/jira_v3_probe.py
uv run python scripts/jira_v3_probe.py --write-test TEST-123
```

Результат сохранить в `docs/jira-v3-spike.md` **без токена и пароля**.

#### 1.3. Что должно стать известно

1. Проходит ли basic auth с текущими `login` / `pass` на Cloud?
2. `deploymentType` — `Cloud`?
3. `description` и `comment` — `dict` (ADF) или `str`?
4. Ломается ли `startAt`-пагинация?
5. Падает ли v3 на string-комментарии и проходит ли ADF?
6. Работают ли `currentUser()` в JQL для `assignee` и `worklogAuthor`?
7. Нужно ли обновлять креды (email + API token вместо пароля)?

#### DoD шага 1

- Скрипт создан и запущен.
- Вывод сохранён в `docs/jira-v3-spike.md` без секретов.
- Есть ответы на 7 вопросов выше.
- `src/` и `tests/` не изменены.
- `git status` показывает только `scripts/jira_v3_probe.py` и
  `docs/jira-v3-spike.md` (или скрипт не коммитится).
- **Коммит**: `docs: record jira v3 spike` (опционально; скрипт можно
  оставить untracked).

---

### Шаг 2: `exceptions.py` + отказ от `exit()`

**Цель**: интеграции не завершают процесс, а поднимают типизированные
исключения.

- Создать `src/lit/exceptions.py`:

  ```python
  class LitError(Exception): ...
  class JiraIntegrationError(LitError): ...
  class GitLabIntegrationError(LitError): ...
  class ConfigError(LitError): ...
  ```

- В `jira_connect()` и `load_tasks_from_jira()` заменить `exit()` на
  `raise JiraIntegrationError(...) from e`.
- В `src/lit/__init__.py` на границе CLI ловить `LitError`, печатать в
  `stderr`, возвращать `exit(1)`.
- **Коммит**: `refactor(integrations): raise LitError instead of exit()`.

#### DoD

- `grep -n "exit()" src/lit/integrations/*.py` → пусто.
- Новые тесты на исключения.
- Smoke `exit=0`.

---

### Шаг 3: `plain_text_to_adf()`

**Цель**: чистая функция конверсии plain text → ADF для worklog comment.

- Создать `src/lit/integrations/adf.py`.
- Поведение:
  - пустая строка → `{"type": "doc", "version": 1, "content": []}`;
  - каждая непустая строка → `paragraph` с одним `text`-узлом;
  - пустая строка между абзацами → пустой `paragraph`, **без**
    `{"type": "text", "text": ""}`;
  - `\r\n` нормализуется, управляющие символы не ломают ADF.
- Тесты: `tests/test_adf.py` — одна строка, несколько строк, пустые
  строки, пустой ввод, `\r\n`.
- **Коммит**: `feat(integrations): add plain_text_to_adf for Jira v3`.

#### DoD

- Новые тесты зелёные.
- `plain_text_to_adf("hi")` возвращает валидный ADF.
- Покрытие `adf.py` — 100%.

---

### Шаг 4: `jira_client.py` — единый клиент

**Цель**: одна точка подключения для pull и push.

- Создать `src/lit/integrations/jira_client.py`:
  - `resolve_api_version(cfg, jira=None) -> str`;
  - `build_jira(cfg=None) -> JIRA`;
  - `search_all_issues(jira, jql, fields) -> list`;
  - `format_jira_error(exc) -> str`.
- Выбор версии:
  - `[jira] api_version = auto | 2 | 3`, default `auto`;
  - `auto`: Cloud → `3`, Data Center → `2`;
  - явный `2` / `3` имеет приоритет;
  - если v3-клиент на DC падает с `400/404`, fallback на v2.
- `search_all_issues`:
  - Cloud: `enhanced_search_issues` с `nextPageToken` или
    `maxResults=False`;
  - DC: `search_issues` с `maxResults=False` / `startAt`.
- Тесты с моками `JIRA`, без сети.
- **Коммит**: `feat(integrations): add jira client factory with api version`.

#### DoD

- Тесты на `auto`, явные `2`/`3`, fallback.
- `jira_client.py` покрыт ≥90%.
- Smoke `exit=0`.

---

### Шаг 5: Push — ADF и `Worklog`

**Цель**: `lit push` корректно работает на v2 и v3.

- `jira_push.py` использует `build_jira()` из `jira_client.py`.
- `add_worklog()`:
  - при `api_version == "3"` → `comment = plain_text_to_adf(comment)`;
  - при `"2"` → строка;
  - возвращает `str(worklog)` / `worklog.id`, а не объект;
  - `JIRAError` → `JiraIntegrationError` с понятным сообщением.
- Тесты:
  - v2 → `comment` строка;
  - v3 → `comment` dict с `type == "doc"`;
  - ошибка `401` / `404` / timeout;
  - `Worklog` нормализуется в id.
- **Коммит**: `feat(integrations): use ADF for worklog comment on Jira v3`.

#### DoD

- v2 и v3 тесты зелёные.
- `jira_push.py` покрыт ≥90%.
- Smoke `exit=0`.

---

### Шаг 6: Pull — `currentUser()` и пагинация

**Цель**: `lit pull --jira` работает на Cloud и DC.

- `jira.py` использует `build_jira()` и `search_all_issues()`.
- Убрать `TARGET_USER`:
  - `assignee = currentUser()`;
  - `worklogAuthor = currentUser()`;
  - если `currentUser()` не подходит — email/логин из конфига.
- Убрать ручной цикл `startAt`.
- Убрать мёртвый код в `save_commits` / цикле `TASKS`.
- Ошибки — через `JiraIntegrationError`.
- Тесты с фейковым клиентом:
  - Cloud-пагинация;
  - DC-пагинация;
  - пустой результат;
  - ошибка поиска.
- **Коммит**: `fix(integrations): repair jira pull pagination and currentUser jql`.

#### DoD

- `lit pull --jira` на реальном Cloud возвращает задачи.
- Нет `NameError` и `startAt`-цикла.
- `jira.py` покрыт ≥80%.
- Smoke `exit=0`.

---

### Шаг 7: Конфиг, `init`, CLI-граница, документация

- `config_manager.get_jira()`:
  - добавить `api_version` (`auto` / `2` / `3`);
  - `email` как fallback для `login`.
- `init.py`:
  - для Cloud — подсказка «email + API token»;
  - для DC — «login + password/PAT»;
  - ссылка на создание токена Atlassian.
- `src/lit/__init__.py`: обработка `LitError` на границе CLI.
- `README.md`: секция `[jira]`, `api_version`, Cloud/DC auth.
- `REFACTORING.md`: актуализировать после spike.
- **Коммит**: `feat(config): add jira api_version and cloud token guidance`.

#### DoD

- `lit init` не ломает существующий конфиг.
- README соответствует поведению.
- Smoke `exit=0`.

---

### Шаг 8: Сценарии ошибок + реальный smoke

**Цель**: покрыть пути, которые ломаются при переключении v2↔v3.

- Тесты:
  - `401` → `JiraIntegrationError` с подсказкой про email/API token;
  - `403` → нет прав;
  - `404` → неверный URL/endpoint;
  - timeout → `JiraIntegrationError`;
  - пустой ответ поиска → `{}` / пустой список без падения.
- Реальный smoke:
  - `lit pull --jira` на Cloud;
  - `lit push` на тестовой задаче;
  - проверить комментарий в Jira;
  - убедиться, что worklog удаляется/не остаётся мусора.
- **Коммит**: `test(integrations): cover jira error scenarios`.

#### DoD

- Все сценарии покрыты тестами.
- Реальный pull/push подтверждён.
- `git status` чистый.

## 8. Что исправлено по сравнению со старой версией плана

- Baseline: **48 тестов / 72%**, а не 44 / 82%.
- `cli.py` не существует — CLI в `src/lit/__init__.py`.
- Добавлены `TARGET_USER` и пагинация `startAt` — без них переход
  бессмысленен: `lit pull` уже сломан.
- `add_worklog()` возвращает `Worklog`, а не строку.
- ADF: пустые строки не должны превращаться в пустые `text`-узлы.
- Убрана работа с `description` — `lit` его не использует.
- Добавлен единый `jira_client.py` вместо двух копий подключения.
- Учтено, что `docs/refactoring-log.md` отсутствует.

## 9. Дальнейшие шаги (вне цикла)

- `WorklogEntry` dataclass и разбор `.litstore`.
- Перенос CLI из `__init__.py` в `cli.py` с сохранением re-export для
  `patch("lit.X")`.
- ADF → plain text для чтения комментариев.
- GitLab: проверить актуальность v4.
- Auto-update (см. `UPDATE.md`).
