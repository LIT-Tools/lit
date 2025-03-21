# LIT: Logging Integrated Timekeeper

<img src="https://img.shields.io/badge/python-3.9+-blue?logo=python" alt="Python Version"> <img src="https://img.shields.io/badge/license-MIT-green" alt="License"> <img src="https://img.shields.io/badge/coverage-51%25-yellow" alt="Coverage">

Консольная утилита для удобного управления рабочими логами с интеграцией Jira и GitLab

```
┌LIT>────────┐
│ TSK 8h ─○─ │ 
└─────────\\─┘
```

LIT — это консольная утилита для удобного управления ворклогами с интеграцией Jira и GitLab, вдохновлённая поведением Git.

Она помогает быстро и удобно вносить записи рабочего времени, предварительно сохраняя их в локальном файле, а затем отправлять в Jira. Помимо основных возможностей логирования, LIT поддерживает автодополнение команд, для быстрой и комфортной работы.
## 🚀 Основные команды

### Добавление записи
```bash
lit add <код_задачи> <время> "<сообщение>" [опции]

# Поддерживаемые форматы времени:
# 1h (1 час) | 30m (30 минут) | 1d (8 часов) | 1h 15m | 4 (4 часа)

# Примеры:
lit add TASK-1752 4 "Убрал из меню ссылку О компании"
lit add TASK-15 "1h 30m" "Исправление крэша" -d 25.12.2023
lit add BUG-404 2d "Рефакторинг модуля"
```

**Параметры:**
- `код_задачи` - код задачи в Jira (формат: XXX-123)
- `время` - продолжительность работы (форматы: 1h, 30m, 2d, '1h 30m')
- `сообщение` - описание выполненной работы

**Опции:**
- `-d --date` - дата (по умолчанию: текущая)
- `-t --time` - время начала (по умолчанию: текущее)

### Интерактивный режим с автодополением 
```bash
lit
# let>
```

### Просмотр статуса
```bash
lit status
```
Выводит список всех подготовленных записей с группировкой по датам.

### Отправка логов
```bash
lit push
```
Отправляет все подготовленные записи в Jira после подтверждения.

### Редактирование записей
```bash
lit edit
```
Открывает файл `.litstore` в системном редакторе для ручного редактирования.

### Синхронизация данных
```bash
lit pull [--jira] [--gitlab]
```
- `-j --jira` - загрузить задачи из Jira
- `-g --gitlab` - загрузить коммиты из GitLab

### Вспомогательные команды
`-v --version` - версия приложения  
`-h --help` - описание команд

## ⚙️ Конфигурация

`lit init` - вызывает интерактивное создание конфигурационного файла

Пример `~/.lit/.litconfig`:
```ini
[user]
login = user
email = user@domain.com

[jira]
login = user
email = user@domain.com
pass = password
url = https://jira.com
days = 30

[gitlab]
login = user
email = user@domain.com
url = https://gitlab.com
token = ваш_личный_токен
days = 30
```

## 📂 Формат хранения данных

Подготовленные записи хранятся в текстовом файле `.litstore`:
```
12.02.2025 [10:00 - 14:00] TASK-1752 4h `Убрал из меню ссылку О компании`
25.12.2023 [14:30 - 15:00] TASK-15 30m `Исправление крэша при загрузке`
```

Отправленные логи сохраняются в `.lithistory` с ID ворклога:
```
12.02.2025 [10:00 - 14:00] TASK-1752 4h `...` # 779121
```

## 📦 Установка из исходников

### 🍏 Mac
```bash
# Установка Poetry (рекомендуется через Homebrew)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install poetry

#  Для управления версиями Python (опционально, но рекомендуется)
brew install pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Установка нужной версии Python (пример для 3.12)
pyenv install 3.12
pyenv global 3.12

git clone https://github.com/LIT-Tools/lit.git
cd lit

poetry install
source .venv/bin/activate  # Для bash/zsh
```

### 🐧 Linux
*WIP...*

### 🪟 Windows

PowerShell:
```bash
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
\* *В PS может потребоваться разрешение на запуск локальных скриптов*

```bash
git clone https://github.com/LIT-Tools/lit.git
cd lit
poetry install
.\.venv\Scripts\activate
# or
poetry env activate 
```

## 🔨 Сборка
Windows / Linux / macOS
```bash
poetry run pyinstaller lit.spec
```

## 🛠 Тестирование

1. Установите dev-зависимости:
```bash
poetry install --with dev
```

2. Запустите тесты:
```bash
coverage run -m unittest discover
coverage report -m
```

3. Откройте отчёт:
```bash
# Windows
coverage html; Start-Process "htmlcov/index.html"

# Linux/Mac
coverage html && xdg-open htmlcov/index.html
```

## 🔮 Планы развития

- [ ] Исправить подсказки ключей для команды `add`, убрать ложные срабатывания
- [x] Настроить сборку бинарника
- [x] Опубликовать в интернете для установки
- [x] Настроить версионирование
- [ ] Рефакторинг дублирующего кода
- [ ] Рефакторинг архитектуры под классический питонячий формат 
- [ ] Повысить покрытие тестами 80+%
- [x] Понизить версию питона 

### 🤔 Возможное функции, но под вопросом:

Настройка конфигурации из консоли 
`lit config` показывает конфиг
`lit config add <key> <value>` добавляет запись 

В кофиге есть поле `start_time` с непустым значением и пользователь не предал значение через ключ -h 
то используем start_time как начальное время лога. Это защита если спец будет вносить логи поздно ночью

## ⚠️ Особенности работы валидации

- Время начала позже 19:00 или раньше 5:00 вызывает предупреждение
- При указании несуществующей задачи в автодополнении, появится подтверждение
- Поддержка сложных временных форматов (1d = 8h, 1h 15m и т.д.)

## ❓ Частые вопросы

**Q: Как указать время больше 24 часов?**  
A: Используйте дни (`d`):  
```bash
lit add TASK-777 3d "Марафон разработки"
```

---

*Разработано с ❤️ для упрощения рутинных задач*<br>
*Лицензия: MIT*
