# Рефакторинг: текущее состояние и план

## Следующий шаг: переезд на `src/lit/`

Цель — классический питонячий layout: пакет в `src/lit/`, тесты в
`tests/`, `pyproject.toml` управляет сборкой. Без дробления `cli.py`
на `cli/commands/*`, без новых абстракций.

```
src/lit/
├── __init__.py             # из cli.py: cli, main (re-export для entry point)
├── __main__.py             # python -m lit
├── cli.py                  # бывший lit.py
├── constants.py
├── config_manager.py
├── init.py
├── parser.py
├── utils.py
├── core/
│   ├── __init__.py
│   └── worklog_manager.py
└── integrations/
    ├── __init__.py
    ├── jira.py
    ├── jira_push.py
    └── gitlab.py

tests/      
├── test_lit.py               # тестирует cli
├── test_init.py        
├── test_import_gitlab.py     # переименование в test_gitlab.py — отдельным коммитом
└── test_push.py              # переименование в test_jira_push.py — отдельным коммитом
```

Что меняется:
- `pyproject.toml`: `packages = ["src/lit"]` + `sources = ["src"]`,
  убрать `only-include` со списком плоских модулей;
- `pyproject.toml`: добавить `[tool.coverage.run]` с
  `source = ["src/lit"]` и `omit = ["tests/*"]` — чтобы покрытие
  считало только код;
- `entry point` остаётся `lit = "lit:cli"`, но `cli` теперь
  ре-экспортируется из `src/lit/__init__.py`;
- тесты: `git mv test_*.py tests/` — импорты **не меняются**, они уже
  пишут `from lit.core.worklog_manager import ...`, а `lit` установлен
  editable через `uv sync`;
- `unittest discover` из корня находит `tests/` рекурсивно — команды
  в README не меняются;
- `git mv` для исходников — сохраняет историю.

## Отложенные улучшения (не сейчас, но обсуждено)

- **`core/models.py`** — `WorklogEntry` dataclass вместо `dict` в
  `add_entry`/`pars_store`/`push_entries`. Реальное улучшение
  типизации, но это рефакторинг **логики**, а не перемещение —
  отдельный цикл.
- **`core/parsing/lit_store_parser.py`** — `parser.py` переедет туда
  при переезде на `src/` (логично, но не блокер).
- **`cli/commands/*`** — разбить `cli.py` на модули по командам.
  Сейчас 6 команд, `if/elif` в `process_arguments` читается лучше
 6 файлов. Откладываем, пока команд не станет >10.
- **`tests/unit/` + `tests/integration/`** — разделить тесты по
  типу. Сейчас все 44 — unit с моками; разделять нечего. Появится
  настоящий integration-тест (живой Jira/GitLab) — тогда разделим.
- **`storage/profile_manager.py`** — реализация мультипрофиля.
  Отдельная задача, см. `MULTI-PROFILE.md` (draft).