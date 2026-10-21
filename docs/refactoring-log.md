## Шаг 0 — починка упаковки и entry point (2026-10-20)

### Результат
- `pyproject.toml`: `[project.scripts] lit = "lit:cli"` + `[tool.hatch.build.targets.wheel] only-include` со списком плоских модулей. Коммит `635d035 build(packaging): fix wheel to include flat modules`.
- `lit.py`: обёртка `cli()` → `process_arguments()`, `__main__` делегирует в `cli()`. Коммит `72dc7c4 fix(cli): add entry-point wrapper ...`.

### Где буксовал
- После первого фикса упаковки `uv run lit --help` дошёл до `main()` и упал:
  `TypeError: main() missing 1 required positional argument: 'parser'`.
  Выяснилось: `main(parser)` — это REPL, настоящая точка входа CLI — `process_arguments()`.
- `.venv` приезжал с linux-путём (`/root/.local/share/uv/python/...`),
  uv его пересоздавал и подхватывал pyenv-питон (`/Users/.../.pyenv/...`)
  вместо своего managed CPython.

### Правила для следующих шагов
- После любой правки `pyproject.toml` — `uv sync --reinstall-package lit`,
  иначе `.venv/bin/lit` остаётся старым.
- Любой вывод команды сопровождать `echo exit=$?`; traceback = провал,
  даже если exit=0.
- Если в `.venv/bin/python` битый симлинк (linux-путь, pyenv-путь) —
  `rm -rf .venv && uv sync` (или один раз `uv python pin 3.12`, чтобы
  uv брал свой CPython, а не pyenv'шный).

### Чего не делать
- Не редактировать `.venv/` руками и не использовать `git reset` (в т.ч.
  `--soft`) для «переписать сообщение» — только новый коммит или
  `git commit -F -`.

### Команды, которые сэкономили время
- `git show --stat HEAD` — проверить, что в коммите ровно ожидаемые файлы
  (атомарность).
- `git log --oneline -3` — убедиться, что HEAD на месте и предыдущие
  коммиты не задеты.

## Шаг 1 — вынос путей `.lit` в `constants.py` (2026-10-20)

### Результат
- `constants.py`: определения `LIT_DIR`, `LIT_STORE`, `LIT_HISTORY`, `CONFIG_FILE`, `COMMITS_FILE`, `TASKS_FILE` + `os.makedirs(LIT_DIR, exist_ok=True)`. Коммит `467f395 refactor(constants): extract shared paths into constants.py`.
- `lit.py`, `import_jira.py`, `import_gitlab.py`, `push.py`, `init.py`: дублирующиеся определения путей заменены на импорт из `constants.py`.

### Где буксовал
- (нет)

### Правила для следующих шагов
- После правки путей — сразу тесты + smoke (`uv run coverage run -m unittest discover && uv run lit --help`).
- Не менять `load_config()`, `WorklogManager`, формат типов путей.
- Если тесты упали на тип `LIT_*` — переключиться на одну форму (Path vs str).

### Чего не делать
- Не запускать интерактивные команды (`uv run lit init`, `push`, `add`), если это не smoke.

## Шаг 2 — централизация конфигурации (`config_manager.py`) (2026-10-21)

### Результат
- Создан `config_manager.py` с функциями чтения конфига:
  - `load_config(path=None)` — базовый reader, возвращает `RawConfigParser`;
  - `get_user(cfg=None)` — секция `[user]`: login/email/editor;
  - `get_jira(cfg=None)` — секция `[jira]`: login/email/pass/url/days;
  - `get_gitlab(cfg=None)` — секция `[gitlab]`: login/email/url/token/days.
- Переписаны: `lit.py`, `import_jira.py`, `import_gitlab.py`, `push.py`, `init.py`.
- Удалён TODO-комментарий `#TODO Конфигурация дублируется, вынести в отдельный код`.
- Сохранена возможность моков тестов через алиасы `load_config()` в `lit.py` и `import_gitlab.py`
  (не меняли сами тесты). Коммит `c09aa30 refactor(config): centralize configuration loading in config_manager.py`.

### Где буксовал/риски
- **Алиасы для совместимости**: некоторые файлы (`lit.py:29`, `import_gitlab.py:154`) продолжают
  иметь свою `def load_config()` — это намеренные алиасы, чтобы тесты (мокающие по имени/модулю)
  не падали. Это паттерн, а не ошибка дублирования.
- **`init.py`**: там используется `ConfigParser` для **записи** конфига — это разрешено, проверка
  запрещает только дублирование чтения конфигов.

### Правила для следующих шагов (после шага 2)
- Не трогать `WorklogManager`, `main()`, `process_arguments()`, `cli()`.
- Если нужно рефакторить дальше — сначала обсудить новый уровень абстракции.
- После правок конфигов/интеграций: smoke (`--help`, `-v`, `status`) + тесты с покрытием.

### Чего не делать
- Не создавать новые директории (`core/`, `integrations/`), если в ТЗ этого нет явно.
- Не менять формат путей в `constants.py` (это уже готово).
- Не добавлять type hints сейчас — это следующий этап.

## Шаг 3 — вынос `WorklogManager` в `core/worklog_manager.py` (2026-10-21)

### Результат
- Создан пакет `core/`: `core/__init__.py` (пустой) + `core/worklog_manager.py` (199 строк).
  Класс `WorklogManager` вместе со `@staticmethod _configure_add_parser` перенесён **дословно**.
- `lit.py` похудел на 266 строк: `class WorklogManager` удалён, добавлен re-export
  `from core.worklog_manager import WorklogManager` (`lit.py:18`) — чтобы `main()`,
  `process_arguments()` и `create_argument_parser()` продолжали находить класс через
  глобальный lookup модуля `lit`, а тесты — через `lit.WorklogManager`.
- В `lit.py` остались: `WorklogCompleter`, `main`, `cli`, `create_argument_parser`,
  `process_arguments`, `get_version`, алиас `load_config()`, глобалы `COMMITS`/`TASKS`/`CUSTOM_EDITOR`.
- Коммит `3c00846 refactor(core): move WorklogManager to core/worklog_manager.py`.

### Таблица мок-совместимости (главное правило шага)
Тесты мокают через `lit.<имя>`, поэтому **потребитель в `core/worklog_manager.py`
должен импортировать имя лениво, внутри метода**:

| Имя | Где мокают | Стратегия в `core/worklog_manager.py` |
|-----|-----------|-------------------------------------|
| `TASKS` | `lit.TASKS` | lazy `from lit import TASKS` в `add_entry` |
| `add_worklog` | `lit.add_worklog` | lazy `from lit import add_worklog, jira_connect` в `push_entries` |
| `jira_connect` | `lit.jira_connect` | там же |
| `load_tasks_from_jira` | `lit.load_tasks_from_jira` | lazy `from lit import load_tasks_from_jira, load_commits_from_gitlab` в `pull_entries` |
| `load_commits_from_gitlab` | `lit.load_commits_from_gitlab` | там же |
| `init_config` | `lit.init_config` | lazy `from lit import init_config` в методе `init_config` |
| `pars_store` | не мокают | top-level `from parser import pars_store` — ОК |
| `sort_key` | не мокают | top-level `from utils import sort_key` — ОК |

Топ-левел `from push import jira_connect` в `core/worklog_manager.py` **сломал бы** `patch("lit.jira_connect")`:
мок патчится в модуле `lit`, а потребитель смотрит в `push`. Только deferred-импорт
(`from lit import jira_connect` внутри метода) связывает потребителя с `lit`.

### Точечные правки при переносе (2 шт.)
1. `edit_entries`: вместо `load_config()` + глобальной `CUSTOM_EDITOR` — `get_user()["editor"]`
   из `config_manager` (deferred-импорт не нужен, `config_manager` не мокается).
2. `add_entry`: `TASKS` остался в `lit.py` → `from lit import TASKS` внутри метода
   (иначе циклический импорт `lit → core.worklog_manager → lit.TASKS`).

### Где буксовал
- **Циклический импорт**: `lit.py` делает `from core.worklog_manager import WorklogManager` на
  верхнем уровне, а `core/worklog_manager.py` не может делать `from lit import ...` на верхнем
  уровне — только внутри методов. Проверка: `uv run python -c "import lit"` и
  `uv run python -c "import core.worklog_manager"` → оба `ok`.
- **Re-export ≠ дублирование**: в `lit.py` остаётся строка
  `from core.worklog_manager import WorklogManager` — это единственный способ сохранить
  `lit.WorklogManager` для тестов и `create_argument_parser()`.
- **`PromptSession` в `push_entries`**: в `lit.py` он импортирован сверху, в новом модуле
  пришлось импортировать локально (`from prompt_toolkit import PromptSession` в методе) —
  тест мокает `lit.PromptSession`, а не `prompt_toolkit.PromptSession`.
- **Потеря коммитов из-за `git reset`**: во время работы ветка `feature/refactoring` была
  сброшена к `6e7e7ed` (`git reset --hard`), и 7 коммитов (шаги 0–2) пропали из `git log`,
  хотя физически остались в reflog и в `.git/objects`. Восстановлено так:
  ```bash
  git stash push -m "step 3 changes"   # сохранить текущую работу
  git reset --hard 096b2a2            # вернуть tip утраченной цепочки (из reflog)
  git stash pop                        # наложить изменения поверх
  ```
  После `git reset --hard` **нельзя** делать `git clean -fd` — новые (untracked) файлы
  текущего шага (`core/`) удаляются безвозвратно и в стеш не попадают
  (`git stash` без `-u` не трогает untracked). Это стоило одного потерянного
  `core/worklog_manager.py`, который пришлось пересоздавать вручную.
- **Дата-баги в тестах (НЕ связаны с шагом 3)**: 5 тестов падают и на чистом `096b2a2`
  без каких-либо правок этого шага — тесты ждут фиксированную дату `15.01.2023`,
  а код берёт `datetime.now()` (получается `21.10.2026`):
  `test_unix_editor_from_env`, `test_windows_default_editor`, `test_push_command`,
  `test_push_command_cancel`, `test_two_entries_success`.
  Плюс расхождение путей: тесты ждут `/fake/path/.litstore`, код берёт `~/.lit/.litstore`.
  Требует отдельного решения (править тесты или дефолтную дату) — на шаге 3 не чинили.
- **Smoke `uv run lit --help` падает**: `TypeError: main() missing 1 required positional
  argument: 'parser'`. Entry point в `pyproject.toml` — `lit = "lit:main"`, а `main(parser)` —
  это REPL; настоящая точка входа — `process_arguments()`/`cli()`. Коммит `72dc7c4`
  «fix(cli): add entry-point wrapper...» должен был это починить — но после сброса ветки
  его часть потерялась. Требует проверки перед следующим шагом.

### Правила для следующих шагов
- Перед любыми правками: `git status` должен быть чистым. Если в `git log` нет коммитов
  предыдущих шагов — смотреть `git reflog --all`, а не паниковать: коммиты там есть.
- **`git clean -fd` опасен** во время рефакторинга — сносит untracked-файлы текущего шага
  (`core/`), которые нигде не закоммичены. Если нужно — `git clean -fdn` (dry-run) сначала.
- `git stash push -u` вместо `git stash push`, если в работе есть новые файлы.
- Мок-совместимость проверять грепом ДО переноса, а не после:
  ```bash
  grep -rn "patch(\"lit\.\|patch('lit\." --include="test_*.py" .
  ```
  Каждое найденное `lit.<X>` → потребитель `X` обязан брать `X` через
  `from lit import X` внутри метода.
- `core/worklog_manager.py` импортирует `config_manager`/`constants`/`parser`/`utils`
  как **top-level** (они плоские модули в корне, `from config_manager import get_user`).
- Новые пакеты (`core/`) надо включать в сборку wheel — в `pyproject.toml` есть
  `[tool.hatch.build.targets.wheel] only-include` со списком плоских модулей
  (см. шаг 0); проверить, что `core/` туда попал, иначе пакет не уедет в дистрибутив.

### Чего не делать
- Не переносить `WorklogCompleter`, `main`, `process_arguments`, `cli`,
  `create_argument_parser`, `get_version`, алиас `load_config`, глобалы
  `COMMITS`/`TASKS`/`CUSTOM_EDITOR` — они остаются в `lit.py`.
- Не трогать `test_*.py` — при сломанном моке правится потребитель (lazy-импорт),
  а не тест.
- Не добавлять type hints на этом этапе (это отдельный шаг).
- Не создавать `integrations/`, `src/`, `services/` — только `core/`.
- Не запускать `uv run lit` без аргументов, а также `init`/`push`/`add`/`edit` —
  это интерактив или запись на диск.

## Шаг 4 — integrations/ (выполнено)
- Структура: fallback 1-к-1 (jira.py, jira_push.py, gitlab.py)
- Старые файлы: shims через sys.modules (patch-совместимость)
- lit.py: ре-экспорт из integrations.*; core/worklog_manager.py не трогался
- Тесты: 43 OK, smoke exit=0, моки ok, покрытие 83%
- pyproject.toml: добавлены core/*.py, integrations/*.py в only-include
- Коммит: 6ca9782
- Шимы (`import_jira.py`, `import_gitlab.py`, `push.py`) — `sys.modules`-
  подмена: тесты мокают `patch("import_jira.requests")` /
  `from push import add_worklog`, и обычный `from X import *` не связывает
  их с `integrations.*`. `sys.modules[__name__] = _m` делает
  `import_jira is integrations.jira`, поэтому `patch` бьёт в одно место.
- Удаление шимов — в Шаг 4.5 (не в Шаг 6; Шаг 6 — type hints).

## Шаг 4.5 — удаление deprecated-шимов (2026-10-21)

### Результат
- Удалены `import_jira.py`, `import_gitlab.py`, `push.py`; замены в `test_*.py` на `integrations.jira`, `integrations.gitlab`, `integrations.jira_push`; `pyproject.toml` — убраны из `only-include`. Коммит `14f0065`.
- 43 тестов OK, 83% покрытие, smoke `exit=0`.

### Где буксовал / сложности
- `sys.modules`-подмена работала «магически»: `patch("import_jira.requests")` бил в `integrations.jira.requests` до удаления, но после `git rm` — `ModuleNotFoundError`. Пришлось менять **все** упоминания, включая `from push import ...`, `import push`, `patch.object(import_jira, ...)`.
- В `test_push.py` был только `from push import add_worklog`; в `test_import_gitlab.py` — почти весь файл использовал `import_gitlab` напрямую.
- `REFACTORING_LOOP.md` случайно попал в коммит (поменялся чекбокс шага 4.5) — нужно следить за `git status` перед коммитом.
- `uv sync --reinstall-package lit` обязателен после `git rm` + `pyproject.toml`; иначе `.venv/bin/lit` остаётся старым.
- Production-код (`config_manager.py`, `integrations/gitlab.py`) содержал комментарии `# Для совместимости с тестами, мокающими import_gitlab.load_config()` — это не ошибки, а алиасы, не трогал.

## Шаг 5 — понятная ошибка при невалидной дате (2026-10-21)

### Результат
- `core/worklog_manager.py`: `add_entry` — `try/except ValueError` вокруг первого `strptime(opts.date, "%d.%m.%Y")`; при ошибке `print(...)` + `return` (без `raise`, чтобы внешний `except Exception` не подхватил повторно); `self.entries.append`/`_save` не выполняются.
- `test_lit.py`: добавлен `test_add_entry_invalid_date` (subTest по 4 невалидным датам, `patch("lit.TASKS")`, `patch.object(manager,"_save")`, проверка `assertIn("Неверная дата")`, `assertNotCalled` save); 44 теста OK.
- Коммит `9c7610b`.

### Где буксовал
- `WorklogManager()` в smoke с `patch` может зависать на загрузке `.litstore` / сетевых вызовах (exit 124/137); проверка через `timeout` + `unittest` надёжнее.
- Важно: `print + return`, не `raise`, иначе общий `except Exception` перехватывает и печатает второе сырое сообщение.
- `opts.time` не трогался (вне задачи); внешние `except Exception`, `raise ValueError` для кода/часов оставлены.

### Правила для следующих шагов
- При валидации дат / времени в `add_entry`: оборачивать конкретный `strptime`, `return` сразу, не `raise`.
- Тесты с `WorklogManager` — всегда мокать `_save`, `lit.TASKS`, `builtins.print`; использовать `subTest` для набора входных значений; `manager.entries = []` перед каждым `subTest`.
- `git status` перед коммитом — проверить нет ли лишних `REFACTORING_LOOP.md` / `docs/` (см. шаг 4.5).
- Не добавлять валидацию в `_configure_add_parser` — задача про runtime-обработку.

### Чего не делать
- Не трогать общий `except Exception` в `add_entry` — он остаётся fallback'ом.
- Не изменять поведение для валидных дат (`25.12.2023`, `29.02.2024` и т.п.).
- Не запускать интерактивные `lit add` / `push` / `init` без `_save`/`TASKS` моков.
