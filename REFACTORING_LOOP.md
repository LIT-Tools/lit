# 🤖 Ralph Loop: Пошаговый пайплайн рефакторинга для Агента

Этот документ предназначен для автономного пошагового рефакторинга проекта `lit`
локальной моделью (Qwen) в цикле Ralph Loop.

> ⚠️ Имена файлов, классов и тестов ниже взяты из текущего состояния репозитория,
> а не из README. Перед запуском агента проверь, что они существуют.
> Источник истины по командам — README.md.

## ⚙️ Главные правила для агента:
1. **Атомарность**: Делай строго **один шаг за раз**. Не пытайся сделать всё сразу.
2. **Проверка**: После каждого шага запускай команду проверки.
3. **Откат**: Если проверка выдала ошибку — исправь код. Если не можешь исправить
   за 1 попытку — откати изменения шага (`git checkout .`).
4. **Коммит**: Работаем в ветке `feature/refactoring`. После успешного прохождения шага сделай git-коммит по стандарту
   *Conventional Commits*.

## 🧰 Предварительная подготовка (один раз)
```bash
poetry shell
git checkout -b feature/refactoring   # если ещё не создана
uv sync                               # dev-группа ставится по умолчанию
```

**Команда проверки для всех шагов** (единая, из README → «Тестирование»):
```bash
coverage run -m unittest discover && coverage report -m
```
**Признак успеха**: `unittest` выводит `OK`, покрытие отображается в отчёте.

---

## 📋 Чек-лист выполнения шагов

- [x] Шаг 0: (prerequisite): Починить упаковку пакета
- [x] Шаг 1: Создание модуля констант (`constants.py`)
- [x] Шаг 2: Централизация конфигурации (`config_manager.py`)
- [x] Шаг 3: Выделение бизнес-логики (`core/worklog_manager.py`)
- [ ] Шаг 4: Структурирование интеграций (`integrations/`)
- [ ] Шаг 5: Улучшение валидации дат и защиты от падений
- [ ] Шаг 6: Добавление аннотаций типов (Type Hints)

---

## 🚀 Подробные шаги для выполнения

### Шаг 0 (prerequisite): Починить упаковку пакета
- **Цель**: Сделать entry point `lit = "lit:main"` рабочим, чтобы `uv run lit --help`
  не падал с `ModuleNotFoundError: No module named 'lit'`.
- **Контекст**: `[tool.hatch.build.targets.wheel] packages = ["lit"]` ищет
  директорию `lit/`, которой нет (проект плоский, `lit.py` в корне). Wheel
  собирается пустым, `uv sync` ставит пустышку, entry point падает.
- **Инструкция**:
  1. В `pyproject.toml` заменить секцию:
     ```toml
     [tool.hatch.build.targets.wheel]
     packages = ["lit"]
     ```
     на:
     ```toml
     [tool.hatch.build.targets.wheel]
     only-include = ["*.py"]
     exclude = ["test_*.py"]
     ```
     (временное решение; при переезде на `src/lit/` секция снова изменится —
     см. «Дальнейшие шаги»)
  2. Пересобрать пакет в venv:
     ```bash
     uv sync --reinstall-package lit
     ```
- **Команда проверки**:
  ```bash
  uv run coverage run -m unittest discover && uv run coverage report -m
  uv run lit --help
  ```
- **Признак успеха**: `OK` в тестах **и** `uv run lit --help` печатает справку
  без `ModuleNotFoundError`.
- **Коммит**: `build(packaging): fix wheel to include flat modules`

### Шаг 1: Создание модуля констант (`constants.py`)
- **Цель**: Убрать дублирование путей к директории `.lit` и файлам хранилища.
- **Инструкция**:
  1. Создай файл `constants.py` в корне проекта.
  2. Перенеси туда инициализацию путей:
     ```python
     from pathlib import Path

     LIT_DIR = Path("~/.lit").expanduser()
     LIT_STORE = LIT_DIR / ".litstore"
     LIT_HISTORY = LIT_DIR / ".lithistory"
     CONFIG_FILE = LIT_DIR / ".litconfig"
     COMMITS_FILE = LIT_DIR / "commits.json"
     TASKS_FILE = LIT_DIR / "tasks.json"
     ```
  3. Замени импорты и переменные `LIT_DIR`, `LIT_STORE` и т.д. в `lit.py`,
     `import_jira.py`, `import_gitlab.py`, `push.py`, `init.py` на импорт из
     `constants.py`.
- **Команда проверки**:
  ```bash
  coverage run -m unittest discover && coverage report -m
  ```
- **Признак успеха**: `OK`, все тесты зелёные.
- **Коммит**: `refactor(constants): extract shared paths into constants.py`

---

### Шаг 2: Централизация конфигурации (`config_manager.py`)
- **Цель**: Вынести логику чтения конфига через `configparser` в отдельный компонент.
- **Инструкция**:
  1. Создай файл `config_manager.py`.
  2. Реализуй функцию/класс для безопасного чтения `.litconfig` с сохранением
     регистра (`optionxform`).
  3. Замени дублирующиеся реализации `load_config()` в других файлах на новый
     менеджер.
- **Команда проверки**:
  ```bash
  coverage run -m unittest discover && coverage report -m
  ```
- **Признак успеха**: `OK`, тесты конфигурации и остальные зелёные.
- **Коммит**: `refactor(config): centralize configuration loading`

---

### Шаг 3: Выделение бизнес-логики (`core/worklog_manager.py`)
- **Цель**: Разгрузить `lit.py`, перенеся класс `WorklogManager` в пакет `core/`.
- **Инструкция**:
  1. Создай директорию `core/` с файлом `core/__init__.py`.
  2. Создай `core/worklog_manager.py` и перенеси туда класс `WorklogManager`
     вместе с методами (add, status, push, edit, pull и т.д.).
  3. Импортируй `WorklogManager` в `lit.py`.
- **Команда проверки**:
  ```bash
  coverage run -m unittest discover && coverage report -m
  ```
- **Признак успеха**: `OK`, тесты CLI зелёные без изменений.
- **Коммит**: `refactor(core): move WorklogManager to core/worklog_manager.py`

---

### Шаг 4: Структурирование интеграций (`integrations/`)
- **Цель**: Сгруппировать работу с внешними API (Jira, GitLab) в `integrations/`.
- **Инструкция**:
  1. Создай директорию `integrations/` с файлом `integrations/__init__.py`.
  2. Перенеси туда `import_jira.py`, `import_gitlab.py` и логику из `push.py`.
  3. Поправь импорты в `core/worklog_manager.py` и `lit.py`.
- **Команда проверки**:
  ```bash
  coverage run -m unittest discover && coverage report -m
  ```
- **Признак успеха**: `OK`, тесты интеграций и push зелёные.
- **Коммит**: `refactor(integrations): move external integrations to integrations/`

---

### Шаг 5: Улучшение валидации дат и защиты от падений
- **Цель**: Обрабатывать невалидные даты (например, 31 февраля) понятным
  сообщением вместо падения с `ValueError`.
- **Инструкция**:
  1. В методе добавления записи оберни парсинг даты через `datetime.strptime`
     в `try-except`.
  2. При ошибке выводи понятное сообщение (`⛔ Ошибка: Неверная дата...`) и
     прерывай выполнение, не ломая приложение.
  3. Добавь тест на невалидную дату в существующий тестовый модуль
     (в README имя не зафиксировано — уточни по репо).
- **Команда проверки**:
  ```bash
  coverage run -m unittest discover && coverage report -m
  ```
- **Признак успеха**: новый тест отрабатывает, `OK`, остальные тесты зелёные.
- **Коммит**: `fix(validation): handle invalid calendar dates gracefully`

---

### Шаг 6: Добавление аннотаций типов (Type Hints)
- **Цель**: Повысить качество кодовой базы и помочь IDE находить ошибки.
- **Инструкция**:
  1. Добавь аннотации типов для аргументов и возвращаемых значений во всех
     ключевых функциях и методах классов в пакетах `core/` и `integrations/`.
  2. Убедись, что тесты по-прежнему проходят (линтер в проекте не настроен —
     в README он не упоминается).
- **Команда проверки**:
  ```bash
  coverage run -m unittest discover && coverage report -m
  ```
- **Признак успеха**: `OK`, все тесты зелёные.
- **Коммит**: `refactor(types): add type hints across core and integrations`
