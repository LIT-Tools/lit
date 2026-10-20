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