# 🤖 Ralph Loop: Переход коннектора Jira на REST API v3

Этот документ — план цикла подготовки и перехода `lit` на Jira Cloud
REST API v3. Предназначен для автономного выполнения локальной моделью
(Qwen) в цикле Ralph Loop.

> ⚠️ Имена файлов/функций — из текущего состояния репозитория
> (`src/lit/` layout, 44 теста OK). Источник истины по командам —
> `README.md`.

## 🎯 Контекст

- Сейчас `lit` использует библиотеку `jira` с `rest_api_version = "2"`
  (default). Jira Cloud перешла на v3, где `comment` в worklog и
  `description` в issue — **ADF (Atlassian Document Format)**, JSON-дерево,
  а не plain text[reference:3][reference:4].
- Библиотека `jira` умеет `options={"rest_api_version": "3"}`, но
  **не конвертирует** plain text в ADF автоматически[reference:5]. Нужна
  своя функция конверсии.
- Без этого текущий коннектор к Cloud-инстансам на v3 либо падает, либо
  молча теряет комментарий ворклога.

**Цель цикла — не «переписать всё», а сделать переход безопасным и
проверяемым.** После цикла — сама фича «поддержка v3» (отдельно).

## ⚙️ Главные правила

1. **Spike ≠ TDD.** Шаг 1 (прототип) — разведка, без тестов. Его
   результат — знание (какой API отвечает, что возвращает), а не код,
   который останется в проекте.
2. **TDD после spike.** Шаги 2–6: сначала красный тест (на подтверждённое
   поведение), потом минимальная реализация до зелёного, потом рефактор.
3. **Атомарность.** Один шаг — один коммит. Не смешивать ADF-конверсию и
   параметризацию API-версии в одном шаге.
4. **Откат.** Если после 3 точечных правок красное — `git checkout . &&
   git clean -fd`, следующая попытка с чистого листа.
5. **Коммит.** Conventional Commits. Ветка `feature/jira-v3`.

## 🧰 Предварительная подготовка (один раз)

```bash
git status                                # чисто
git checkout -b feature/jira-v3           # или продолжай текущую
uv sync
```

**Команда проверки** (единая):
```bash
uv run coverage run -m unittest discover && uv run coverage report -m
```
**Признак успеха**: `44 tests OK` (не меньше), покрытие ≥82%.

**Smoke**:
```bash
uv run lit --help;    echo "exit=$?"
uv run lit -v;        echo "exit=$?"
uv run lit status;    echo "exit=$?"
```

---

## 📋 Чек-лист

- [ ] Шаг 0 (prereq): Baseline
- [ ] Шаг 1: Spike-прототип Jira v3 (ручная проверка)
- [ ] Шаг 2: `plain_text_to_adf()` — TDD
- [ ] Шаг 3: Параметризация `rest_api_version` — TDD
- [ ] Шаг 4: `add_worklog` с ADF для v3 — TDD
- [ ] Шаг 5: `exceptions.py` + отказ от `exit()` — TDD
- [ ] Шаг 6: Покрытие сценариев ошибок Jira — TDD

---

## 🚀 Подробные шаги

### Шаг 0 (prereq): Baseline

- **Цель**: зафиксировать зелёную стартовую точку и хэш для отката.
- **Инструкция**:
  ```bash
  git status
  git branch --show-current
  git log --oneline -3
  git rev-parse HEAD          # в отчёт — точка отката
  uv run coverage run -m unittest discover && uv run coverage report -m
  uv run lit --help; echo "exit=$?"
  uv run lit -v; echo "exit=$?"
  uv run lit status; echo "exit=$?"
  ```
- **Признак успеха**: 44 OK, smoke `exit=0`, дерево чисто.
- **Коммит**: не нужен.

---

### Шаг 1: Spike-прототип Jira v3 (ручная проверка)

**Цель**: узнать, как реально ведёт себя библиотека `jira` с
`rest_api_version="3"` на вашем Cloud-инстансе. **Кода в основном
пакете не трогаем.**

#### 1.1. Создать временный скрипт `scripts/jira_v3_probe.py`

Директория `scripts/` — новая, не часть пакета `lit`, в wheel не уедет.

```python
"""Spike: проверка подключения к Jira Cloud REST API v3.

Одноразовый скрипт. После подтверждения — удалить или переписать
в тесты/реализацию.

Запуск:
    uv run python scripts/jira_v3_probe.py
"""
from jira import JIRA
from lit.config_manager import get_jira

cfg = get_jira()
print("URL:", cfg["url"])
print("Login:", cfg["login"])

jira = JIRA(
    server=cfg["url"],
    basic_auth=(cfg["login"], cfg["pass"]),
    options={"rest_api_version": "3"},
)

print("Подключение OK, версия:", jira._options.get("rest_api_version"))

# 1. Скачать одну задачу (JQL)
issues = jira.search_issues("assignee = currentUser() ORDER BY updated DESC", maxResults=1)
print("Найдено задач:", len(issues))
if issues:
    issue = issues[0]
    print("Ключ:", issue.key)
    print("Summary:", issue.fields.summary)
    print("Тип description:", type(issue.fields.description).__name__)
    print("description (repr):", repr(issue.fields.description)[:500])

# 2. Прочитать worklog (если есть)
if issues:
    wls = jira.worklogs(issues[0].key)
    print("Worklog'ов:", len(wls))
    for wl in wls[:1]:
        print("comment type:", type(getattr(wl, "comment", None)).__name__)
        print("comment (repr):", repr(getattr(wl, "comment", None))[:500])
```

#### 1.2. Запустить и записать результат

```bash
uv run python scripts/jira_v3_probe.py 2>&1 | tee /tmp/jira_v3_probe.log
echo "exit=$?"
```

**Что проверить в выводе:**
- Подключение проходит без `401`/`404`.
- `rest_api_version` = `"3"` (или что вернула библиотека).
- `search_issues` возвращает задачи (не пусто, если у пользователя есть
  задачи).
- `type(issue.fields.description).__name__` — `dict` (ADF) или `str`?
  Для v3 ожидается `dict` (ADF).
- `type(wl.comment).__name__` — аналогично.

**Если на каком-то шаге падает** — записать точную ошибку в отчёт.
Скорее всего, либо `rest_api_version` не подхватился, либо Cloud
требует другую аутентификацию (email+token, а не login+pass — проверить).

#### 1.3. НЕ трогать основной код

- `src/lit/integrations/jira.py`, `jira_push.py` — не менять.
- `tests/` — не менять.
- `scripts/jira_v3_probe.py` — **не коммитить** (либо в `.gitignore`,
  либо удалить после проверки). Это разведка, не артефакт.

#### DoD шага 1

- Скрипт создан, запущен, вывод сохранён.
- В отчёте: `rest_api_version`, тип `description`, тип `comment`,
  любые ошибки.
- **Пользователь вручную подтверждает**, что подключение и скачивание
  работают (или объясняет, что именно не так).
- Основной код не изменён: `git status` показывает только
  `scripts/jira_v3_probe.py` (untracked) или пусто, если удалили.
- **Коммит**: не нужен. Или `chore: add temporary jira v3 probe` с
  пометкой «удалить после шага 2» — на усмотрение пользователя.

---

### Шаг 2: `plain_text_to_adf()` — TDD

**Цель**: чистая функция конверсии plain text → ADF dict для `comment`
в worklog. Без HTTP, без Jira-клиента.

#### 2.1. Красный тест (сначала)

Создать `tests/test_adf.py`:

```python
import unittest
from lit.integrations.adf import plain_text_to_adf


class TestPlainTextToADF(unittest.TestCase):
    def test_single_line(self):
        result = plain_text_to_adf("hello")
        self.assertEqual(result["type"], "doc")
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["content"][0]["type"], "paragraph")
        self.assertEqual(
            result["content"][0]["content"][0]["text"], "hello"
        )

    def test_multiline(self):
        result = plain_text_to_adf("line1\nline2")
        paras = result["content"]
        self.assertEqual(len(paras), 2)
        self.assertEqual(paras[0]["content"][0]["text"], "line1")
        self.assertEqual(paras[1]["content"][0]["text"], "line2")

    def test_empty(self):
        result = plain_text_to_adf("")
        self.assertEqual(result["type"], "doc")
        self.assertEqual(result["content"], [])
```

Запустить — **должно быть `ImportError` / `ModuleNotFoundError`**.
Это красный тест.

#### 2.2. Реализация

Создать `src/lit/integrations/adf.py`:

```python
"""Конверсия plain text -> Atlassian Document Format (ADF)."""
from __future__ import annotations


def plain_text_to_adf(text: str) -> dict:
    """Обернуть plain text в минимальный ADF-документ."""
    if not text:
        return {"type": "doc", "version": 1, "content": []}
    paragraphs = [
        {"type": "paragraph", "content": [{"type": "text", "text": line}]}
        for line in text.split("\n")
    ]
    return {"type": "doc", "version": 1, "content": paragraphs}
```

Прогнать тесты — зелёные.

#### DoD шага 2

- `uv run coverage run -m unittest discover && uv run coverage report -m`
  → 47 OK (44 + 3 новых), `TOTAL` ≥82%.
- `uv run python -c "from lit.integrations.adf import plain_text_to_adf; print(plain_text_to_adf('hi'))"` → `exit=0`.
- **Коммит**: `feat(integrations): add plain_text_to_adf for Jira v3`

---

### Шаг 3: Параметризация `rest_api_version` — TDD

**Цель**: `jira_connect()` умеет принимать/читать `rest_api_version` из
конфига, default `"2"` (совместимость), явно `"3"` для Cloud.

#### 3.1. Обследование

```bash
grep -n "def jira_connect\|JIRA(" src/lit/integrations/jira_push.py
grep -n "rest_api_version\|get_jira" src/lit/integrations/jira_push.py
```

#### 3.2. Красный тест

В `tests/test_jira_push.py` (или новый `tests/test_jira_connect.py`)
добавить тест с моком `jira.JIRA`:

```python
def test_jira_connect_passes_rest_api_version(self):
    from unittest.mock import patch
    from lit.integrations.jira_push import jira_connect

    with patch("lit.integrations.jira_push.JIRA") as mock_jira, \
         patch("lit.integrations.jira_push.get_jira") as mock_cfg:
        mock_cfg.return_value = {
            "url": "https://x.atlassian.net",
            "login": "u",
            "pass": "p",
            "rest_api_version": "3",
        }
        jira_connect()
        _, kwargs = mock_jira.call_args
        self.assertEqual(
            kwargs.get("options", {}).get("rest_api_version"), "3"
        )
```

Тест красный, потому что `jira_connect` не читает `rest_api_version`.

#### 3.3. Реализация

В `jira_connect`:

```python
cfg = get_jira()
options = {"rest_api_version": cfg.get("rest_api_version", "2")}
return JIRA(server=cfg["url"], basic_auth=(cfg["login"], cfg["pass"]), options=options)
```

В `config_manager.get_jira()` добавить чтение `rest_api_version` из
секции `[jira]` (fallback `"2"`).

#### DoD шага 3

- 48 OK (47 + 1), покрытие ≥82%.
- Тест на `rest_api_version="3"` зелёный; тест на default `"2"` (если
  добавили) тоже.
- Smoke: `uv run lit --help / -v / status` → `exit=0`.
- **Коммит**: `feat(integrations): parameterize jira rest_api_version`

---

### Шаг 4: `add_worklog` с ADF для v3 — TDD

**Цель**: при `rest_api_version="3"` `comment` в `add_worklog`
оборачивается в ADF; при `"2"` остаётся строкой.

#### 4.1. Обследование

```bash
grep -n "def add_worklog" -A 30 src/lit/integrations/jira_push.py
```

#### 4.2. Красный тест

```python
def test_add_worklog_v3_uses_adf(self):
    from unittest.mock import patch, MagicMock
    from lit.integrations.jira_push import add_worklog

    jira = MagicMock()
    jira._options = {"rest_api_version": "3"}
    with patch.object(jira, "add_worklog") as mock_add:
        add_worklog(jira, "TASK-1", "4h", "hello", "25.12.2023", "10:00")
        _, kwargs = mock_add.call_args
        self.assertIsInstance(kwargs["comment"], dict)
        self.assertEqual(kwargs["comment"]["type"], "doc")

def test_add_worklog_v2_uses_string(self):
    # тот же сценарий, rest_api_version="2", comment — str
```

Красные: сейчас `comment` — всегда строка.

#### 4.3. Реализация

В `add_worklog`:

```python
version = getattr(jira, "_options", {}).get("rest_api_version", "2")
comment = plain_text_to_adf(message) if version == "3" else message
```

(Точный способ получить версию — по результатам spike шага 1; возможно,
`jira._options` недоступен, тогда передавать версию аргументом из
`push_entries`.)

#### DoD шага 4

- 50 OK (48 + 2), покрытие ≥82%.
- v3 → ADF dict, v2 → str.
- Smoke `exit=0`.
- **Коммит**: `feat(integrations): use ADF for worklog comment on Jira v3`

---

### Шаг 5: `exceptions.py` + отказ от `exit()` — TDD

**Цель**: `jira_connect` поднимает `JiraIntegrationError` вместо
`exit()`. `cli` ловит `LitError`.

#### 5.1. Обследование

```bash
grep -n "exit()\|sys.exit" src/lit/integrations/*.py
grep -n "def jira_connect" -A 20 src/lit/integrations/jira_push.py
```

#### 5.2. Красный тест

```python
def test_jira_connect_raises_on_failure(self):
    from lit.integrations.jira_push import jira_connect
    from lit.exceptions import JiraIntegrationError
    with patch("lit.integrations.jira_push.JIRA", side_effect=Exception("boom")):
        with self.assertRaises(JiraIntegrationError):
            jira_connect()
```

Красный: сейчас `jira_connect` делает `exit()`.

#### 5.3. Реализация

Создать `src/lit/exceptions.py`:

```python
class LitError(Exception): ...
class JiraIntegrationError(LitError): ...
class GitLabIntegrationError(LitError): ...
class ConfigError(LitError): ...
```

В `jira_connect`: `try: ... except Exception as e: raise JiraIntegrationError(str(e)) from e`.
В `cli.py`: обернуть вызов команды в `try/except LitError`, вывести в
`stderr`, `sys.exit(1)`.

#### DoD шага 5

- 51+ OK, покрытие ≥82%.
- `grep -n "exit()" src/lit/integrations/*.py` → пусто.
- Smoke `exit=0`.
- **Коммит**: `refactor(integrations): raise LitError instead of exit()`

---

### Шаг 6: Покрытие сценариев ошибок Jira — TDD

**Цель**: покрыть пути, которые ломаются при переключении v2↔v3:
`401`, `404`, timeout, пустой ответ.

#### 6.1. Красные тесты

В `tests/test_jira_connect.py` / `test_jira_push.py` добавить по одному
тесту на каждый сценарий (мок `JIRA`/`requests`):
- `401` → `JiraIntegrationError` с понятным сообщением;
- timeout → `JiraIntegrationError`;
- `load_tasks_from_jira` при ошибке не падает, а возвращает `{}` или
  поднимает `JiraIntegrationError` (решить по текущему поведению).

#### DoD шага 6

- 54+ OK, покрытие `jira*.py` выросло (не «85%», а «конкретные пути
  покрыты»; см. `coverage report -m`).
- Smoke `exit=0`.
- **Коммит**: `test(integrations): cover jira error scenarios`

---

## 🔮 Дальнейшие шаги (вне цикла)

- **Сама фича «поддержка Jira v3»**: после цикла — включить `"3"` в
  конфиге, прогнать на реальном инстансе, обновить README.
- **GitLab**: проверить, что текущий `integrations/gitlab.py` работает с
  текущим GitLab (v4 стабилен). Если нет — отдельный маленький цикл.
- **`cli.py` из `__init__.py`**: после коннектора, с оговоркой про
  re-export для `patch("lit.X")` (см. `docs/refactoring-log.md`).
- **`core/models.py`** (`WorklogEntry` dataclass) — отдельный цикл.

## 📚 Уроки с прошлых циклов

Полный список — `docs/refactoring-log.md`. Для этого цикла:

- **`patch("lit.X")` работает, пока `X` в namespace `lit`** — не
  переносить `TASKS`/`COMMITS`/`add_worklog` из `__init__.py` в этом
  цикле.
- **`git reset --hard` + `git clean -fd`** — опасная пара; откат
  делать `git checkout . && git clean -fd`.
- **`uv sync --reinstall-package lit`** — после правок `pyproject.toml`
  или перемещения файлов.
- **`echo exit=$?`** на каждой команде; traceback = провал.
- **`from __future__ import annotations`** — первая строка после
  docstring.