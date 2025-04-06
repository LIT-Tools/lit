# Сырой план на рефакторинг

### Итоговая целевая структура проекта:

```
lit/
├── src/
│   ├── lit/                       # Основной пакет
│   │   ├── __init__.py
│   │   │
│   │   ├── cli/                   # Логика CLI
│   │   │   ├── __init__.py
│   │   │   ├── parser.py          # Главный парсер команд (бывший lit.py)
│   │   │   └── commands/          # Реализации команд
│   │   │       ├── __init__.py
│   │   │       ├── add.py
│   │   │       ├── push.py
│   │   │       ├── pull.py
│   │   │       ├── init.py
│   │   │       └── profile.py     # Управление профилями (MULTI-PROFILE.md)
│   │   │
│   │   ├── core/                  # Бизнес-логика
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # Data-классы (WorklogEntry)
│   │   │   ├── worklog_manager.py # Логика работы с ворклогами
│   │   │   └── parsing/
│   │   │       ├── __init__.py
│   │   │       └── lit_store_parser.py  # Парсер .litstore (бывший parser.py)
│   │   │
│   │   ├── integrations/          # Интеграции с внешними системами
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Базовый класс интеграций
│   │   │   ├── jira.py            # Jira-интеграция (бывший push.py + import_jira.py)
│   │   │   └── gitlab.py          # GitLab-интеграция (бывший import_gitlab.py)
│   │   │
│   │   ├── storage/               # Работа с хранилищами
│   │   │   ├── __init__.py
│   │   │   ├── config_manager.py  # Управление конфигами
│   │   │   ├── file_storage.py    # Работа с файлами (.litstore, .lithistory)
│   │   │   ├── profile_manager.py # Управление профилями
│   │   │   └── cache.py           # Кэширование данных (задачи, коммиты)
│   │   │
│   │   └── utils/                 # Вспомогательные утилиты
│   │       ├── __init__.py
│   │       ├── validators.py      # Валидация входных данных
│   │       ├── formatters.py      # Форматирование вывода
│   │       └── decorators.py      # Декораторы для обработки ошибок
│   │
│   ├── tests/                     # Тесты
│   │   ├── __init__.py
│   │   ├── unit/                  # Модульные тесты
│   │   │   ├── test_models.py
│   │   │   └── test_parsing.py
│   │   └── integration/           # Интеграционные тесты
│   │       ├── test_cli.py
│   │       ├── test_jira.py
│   │       └── test_gitlab.py
│   │
│   └── docs/                      # Документация
│       ├── MULTI-PROFILE.md       # Спецификация мультипрофильности
│       └── ARCHITECTURE.md        # Описание архитектуры
│
├── pyproject.toml                 # Конфигурация проекта
├── poetry.lock
├── lit.spec                       # Спецификация для PyInstaller
├── .pre-commit-config.yaml        # Линтеры
├── release-please.yml             # CI/CD
├── CHANGELOG.md
├── LICENSE
└── README.md
```

### Ключевые изменения:
1. **Чёткое разделение ответственности**:
   - `cli/` содержит только логику работы с командной строкой
   - `integrations/` инкапсулирует все внешние API
   - `core/` отвечает за бизнес-логику приложения

2. **Улучшенная поддерживаемость**:
   - Все компоненты изолированы и тестируемы
   - Добавлен модуль `storage/` для централизованного управления данными
   - Утилиты разбиты по функциональному назначению

3. **Мультипрофильность (DRAFT)**:
   - Реализация через `profile_manager.py`
   - Конфиги профилей хранятся в `~/.lit/profiles/`
   - Поддержка связок задач через `MULTI-PROFILE.md`

4. **Безопасность изменений**:
   - Полное покрытие тестами (unit + integration)
   - Интеграция с pre-commit и CI/CD

### Преимущества новой структуры:
1. **Упрощение разработки**:
   ```python
   # Пример использования новой структуры:
   from lit.integrations.jira import JiraIntegration
   from lit.storage.config_manager import ConfigManager

   config = ConfigManager()
   jira = JiraIntegration(config)
   jira.push_worklog(entry)
   ```

2. **Лёгкое расширение**:
   - Добавление новой интеграции (например, GitHub) через наследование от `BaseIntegration`
   - Создание команд CLI через шаблон Command

3. **Прозрачность данных (пока очень поверхностно)**:
   - Все операции с хранилищем через `FileStorage`
   - Автоматическое кэширование через `CacheManager`

4. **Гибкая конфигурация**:
   ```ini
   # Пример мультипрофильного конфига:
   [profiles]
   active = zb

   [zb]
   jira_url = https://jira.company.com
   gitlab_token = glpat-xyz
   ```

Такой подход соответствует принципам чистой архитектуры и позволяет легко масштабировать функционал.