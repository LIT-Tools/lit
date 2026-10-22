# 🤖 Ralph Loop: Переезд на `src/lit/` layout

Этот документ — план следующего цикла рефакторинга `lit`: миграция плоской
структуры на классический `src/`-layout. Предназначен для автономного
выполнения локальной моделью (Qwen) в цикле Ralph Loop.

> ⚠️ Имена файлов и классов ниже — из текущего состояния репозитория.
> Перед запуском проверь, что они существуют. Источник истины по
> командам — `README.md`.

## ⚙️ Главные правила

1. **Атомарность**: один шаг за раз. Не смешивай шаги.
2. **Проверка**: после каждого шага — прогон DoD (тесты + smoke +
   grep'ы).
3. **Откат**: если после 3-х точечных правок красное — откат до
   последнего чистого состояния, следующая попытка с чистого листа.
4. **Коммит**: в ветке `feature/src-layout` (или продолжай
   `feature/refactoring`), Conventional Commits.

## 🧰 Предварительная подготовка (один раз)

```bash
git status                                   # должно быть чисто
git checkout -b feature/src-layout           # или продолжай текущую
uv sync
```

**Команда проверки** (единая):
```bash
uv run coverage run -m unittest discover && uv run coverage report -m
```
**Признак успеха**: `44 tests OK` (не меньше), покрытие ≥82%.

**Smoke** (все три, `exit=0`):
```bash
uv run lit --help;    echo "exit=$?"
uv run lit -v;        echo "exit=$?"
uv run lit status;    echo "exit=$?"
```

---

## 📋 Чек-лист выполнения

- [ ] Шаг 0 (prereq): Baseline — зафиксировать текущее состояние
- [ ] Шаг 1: Переезд исходников в `src/lit/` + `pyproject.toml` + импорты
- [ ] Шаг 2: Переезд тестов в `tests/` + coverage config
- [ ] Шаг 3 (опционально): Переименование тестовых файлов

---

## 🚀 Подробные шаги

### Шаг 0 (prereq): Baseline

- **Цель**: убедиться, что стартовая точка зелёная; зафиксировать хэш
  для отката.
- **Инструкция**:
  1. `git status` — чисто.
  2. `git log --oneline -3` — выписать в отчёт.
  3. Прогнать baseline (команду проверки + smoke).
- **Признак успеха**: 44 OK, smoke `exit=0`, дерево чисто.
- **Коммит**: не нужен.
- **Откат**: n/a.

---

### Шаг 1: Переезд исходников в `src/lit/` (атомарный)

**Цель**: `src/lit/` содержит весь пакет, `lit` установлен editable,
`uv run lit --help / -v / status` работают, тесты зелёные без изменений.

#### 1.1. Создать структуру и переместить файлы

```bash
mkdir -p src/lit
git mv lit.py             src/lit/__init__.py
git mv constants.py       src/lit/constants.py
git mv config_manager.py  src/lit/config_manager.py
git mv init.py            src/lit/init.py
git mv parser.py          src/lit/parser.py
git mv utils.py           src/lit/utils.py
git mv core               src/lit/core
git mv integrations       src/lit/integrations
```

**Почему `lit.py` → `__init__.py`, а не `cli.py`**: тесты мокают через
`patch("lit.TASKS")`, `patch("lit.add_worklog")` и т.д. — вся публичная
поверхность должна остаться в namespace `lit`. Разделение
`__init__.py` на `cli.py` + re-export hub — **отдельный будущий цикл**
(см. «Дальнейшие шаги»), когда можно аккуратно проверить каждый мок.

#### 1.2. Создать `src/lit/__main__.py`

```python
"""Entry point for `python -m lit`."""
from lit import cli

if __name__ == "__main__":
    cli()
```

#### 1.3. Убрать из `src/lit/__init__.py` блок `if __name__ == '__main__'`

В конце файла (было в `lit.py`):
```python
if __name__ == '__main__':
    cli()
```
Для `__init__.py` это dead code (`__name__` не бывает `"__main__"`
при импорте). Функциональность покрывает `__main__.py`. Удалить 2 строки.

#### 1.4. Переписать импорты внутри пакета

В **каждом** `src/lit/**/*.py` заменить плоские импорты на абсолютные
через `lit.`:

| Было | Стало |
|------|-------|
| `from constants import X` | `from lit.constants import X` |
| `from config_manager import X` | `from lit.config_manager import X` |
| `from init import X` | `from lit.init import X` |
| `from parser import X` | `from lit.parser import X` |
| `from utils import X` | `from lit.utils import X` |
| `from core.worklog_manager import X` | `from lit.core.worklog_manager import X` |
| `from integrations.jira import X` | `from lit.integrations.jira import X` |
| `from integrations.jira_push import X` | `from lit.integrations.jira_push import X` |
| `from integrations.gitlab import X` | `from lit.integrations.gitlab import X` |

Найти все места:
```bash
grep -rn "^from \(constants\|config_manager\|init\|parser\|utils\) \|^from core\.\|^from integrations\.\|^import \(constants\|config_manager\|init\|parser\|utils\)" --include="*.py" src/lit/
```

**НЕ менять**:
- deferred lazy-импорты `from lit import TASKS`, `from lit import
  add_worklog, jira_connect`, `from lit import init_config`,
  `from lit import PromptSession` и т.д. в `core/worklog_manager.py` —
  они уже указывают на пакет `lit` (`__init__.py`) и продолжают работать;
- `from __future__ import annotations` — он остаётся первой строкой там,
  где был;
- никаких новых deferred-импортов не вводить.

**Циклический импорт — главный риск**: любой top-level
`from lit import X` в подпакетах (`core/`, `integrations/`) создаст
цикл. В `core/worklog_manager.py` уже всё deferred — не сломать.

#### 1.5. Обновить `pyproject.toml`

Заменить секцию wheel-сборки:

```diff
 [tool.hatch.build.targets.wheel]
-only-include = [
-    "lit.py", "parser.py", "utils.py", "init.py",
-    "constants.py", "config_manager.py",
-    "core/*.py", "integrations/*.py",
-]
+packages = ["src/lit"]
```

(`sources` не нужен — hatchling понимает `src/lit` как пакет `lit`.)

`[project.scripts] lit = "lit:cli"` — **не менять**: `lit.cli` теперь
`src/lit/__init__.py::cli`.

#### 1.6. Пересобрать пакет в venv

```bash
uv sync --reinstall-package lit
```

#### 1.7. Проверки (DoD шага 1)

1. **Тесты**:
   ```bash
   uv run coverage run -m unittest discover && uv run coverage report -m
   ```
   → 44 OK, ≥82%.

2. **Smoke CLI**:
   ```bash
   uv run lit --help;    echo "exit=$?"
   uv run lit -v;        echo "exit=$?"
   uv run lit status;    echo "exit=$?"
   ```
   → все `exit=0`, без traceback.

3. **`python -m lit`** (bonus):
   ```bash
   uv run python -m lit --help;    echo "exit=$?"
   ```
   → `exit=0`.

4. **Импорт с правильным путём**:
   ```bash
   uv run python -c "import lit; print(lit.__file__)";    echo "exit=$?"
   ```
   → путь вида `.../src/lit/__init__.py`, `exit=0`.

5. **`git status` показывает renames**, не delete+add:
   ```bash
   git status --find-renames
   git diff --stat --find-renames HEAD
   ```

- **Коммит**: `refactor: migrate to src/lit/ layout`
- **Откат**: `git checkout . && git clean -fd` — вернуть всё к
  состоянию до шага.

---

### Шаг 2: Переезд тестов в `tests/`

**Цель**: тесты в `tests/`, coverage считает только `src/lit/`,
`discover` находит тесты без флагов.

#### 2.1. Создать директорию и переместить

```bash
mkdir -p tests
git mv test_lit.py             tests/
git mv test_init.py            tests/
git mv test_import_gitlab.py   tests/
git mv test_push.py            tests/
```

Добавить пустой `tests/__init__.py` (нужен для рекурсивного discovery
из корня; без него `unittest discover` без `-s tests` может не найти
тесты):
```bash
touch tests/__init__.py
git add tests/__init__.py
```

**Импорты в тестах не менять** — они используют `from lit import ...` и
`patch("lit.X")`, что после editable-установки работает.

#### 2.2. Обновить `pyproject.toml` — добавить `[tool.coverage.run]`

```toml
[tool.coverage.run]
source = ["lit"]
```

Покрытие теперь считается только для пакета `lit`; тесты в `tests/` в
отчёт не попадают (в старых логах было `test_lit.py ... 95%` — больше
не будет, это правильно).

#### 2.3. Проверки (DoD шага 2)

1. **Тесты**:
   ```bash
   uv run coverage run -m unittest discover && uv run coverage report -m
   ```
   → 44 OK, ≥82%; в отчёте **нет** строк `test_*.py`.

2. **Smoke** — как в шаге 1 (все три + `-m lit`).

3. **`discover` без `-s` находит тесты**:
   ```bash
   uv run python -m unittest discover 2>&1 | grep -E "Ran [0-9]+ tests"
   ```
   → `Ran 44 tests` (не 0).

- **Коммит**: `test: move tests to tests/ directory`
- **Откат**: `git checkout . && git clean -fd` (включая `tests/`).

---

### Шаг 3 (опционально): Переименование тестовых файлов

**Цель**: имена соответствуют текущим модулям.

```bash
git mv tests/test_import_gitlab.py tests/test_gitlab.py
git mv tests/test_push.py          tests/test_jira_push.py
```

#### Проверки (DoD шага 3)

```bash
uv run coverage run -m unittest discover && uv run coverage report -m
uv run lit --help;    echo "exit=$?"
```
→ 44 OK, `exit=0`.

- **Коммит**: `test: rename test files to match current module names`

---

## 🔮 Дальнейшие шаги (вне цикла)

- **Разделить `src/lit/__init__.py` на `cli.py` + re-export hub**.
  Отдельный цикл, требует аккуратной проверки, что все `patch("lit.X")`
  продолжают работать. Скорее всего понадобится либо re-export **и**
  deferred-импорт в `WorklogCompleter` для `TASKS`/`COMMITS`, либо
  оставить `TASKS`/`COMMITS` в `__init__.py`.
- **`core/models.py`** (`WorklogEntry` dataclass) — см.
  `REFACTORING.md` → «Отложенные улучшения».
- **`core/parsing/lit_store_parser.py`** — перемещение `parser.py` в
  подпакет.
- **`cli/commands/*`** — когда команд станет >10.

## 📚 Уроки с прошлого цикла

Полный список — в `docs/refactoring-log.md`. Ключевое для этого цикла:

- **`patch("lit.X")` работает, пока `X` в namespace `lit`** — поэтому
  `lit.py` → `src/lit/__init__.py`, а не `cli.py`.
- **Top-level `from lit import X` в подпакетах = циклический импорт**.
  Только deferred (внутри метода).
- **`uv sync --reinstall-package lit`** — после любой правки
  `pyproject.toml` или удаления/перемещения файлов пакета.
- **`git reset --hard` + `git clean -fd`** — опасная пара; откат
  делать `git checkout . && git clean -fd` (без reset), либо
  `git stash push -u` сначала.
- **Любой вывод — с `echo exit=$?`**. Traceback = провал.
- **`from __future__ import annotations`** — первая исполняемая строка
  после docstring.
- **Проверка атомарности** — `git status --find-renames` (должны быть
  `R`, не `D`+`A`).