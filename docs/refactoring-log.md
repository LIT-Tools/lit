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
