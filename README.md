# LIT: Logging Integrated Timekeeper

[![CRAP](https://img.shields.io/badge/python-3.9+-blue?logo=python)]()
[![CRAP](https://img.shields.io/badge/license-MIT-2E6F40)]()
[![CRAP](https://img.shields.io/badge/coverage-83%25-2E6F40)]() 
[![CRAP](https://img.shields.io/badge/CRAP-8.5-2E6F40)]()

Консольная утилита для удобного управления рабочими логами с интеграцией Jira и GitLab

```
┌LIT>────────┐
│ TSK 8h ─○─ │ 
└─────────\\─┘
```

LIT — это консольная утилита для удобного управления ворклогами с интеграцией Jira и GitLab, вдохновлённая поведением Git.

Она помогает быстро и удобно вносить записи рабочего времени, предварительно сохраняя их в локальном файле, а затем отправлять в Jira. Помимо основных возможностей логирования, LIT поддерживает автодополнение команд, для быстрой и комфортной работы.

## ⏩ Простой старт
CLI вариант:
```bash
lit add TASK-1752 4 "Убрал из меню ссылку О компании"
lit push
```
Интерактивный вариант:
```bash
lit init   # Настраиваем доступы к Jira и GitLab 
lit pull   # Загружаем справочники для подсказок
lit        # Заходим в интерактивный режим 
```

## Установить или скачать

### 🐧 Linux [Download](https://github.com/LIT-Tools/lit/releases/latest/download/lit-linux.tar.gz)

```bash
curl -LO https://github.com/LIT-Tools/lit/releases/latest/download/lit-linux.tar.gz \
&& tar -xzf lit-linux.tar.gz \
&& chmod +x lit \
&& sudo mkdir -p /usr/local/bin \
&& sudo mv lit /usr/local/bin/ \
&& rm lit-linux.tar.gz
```

### 🍏 Mac [Download](https://github.com/LIT-Tools/lit/releases/latest/download/lit-macos.tar.gz)

```bash
curl -LO https://github.com/LIT-Tools/lit/releases/latest/download/lit-macos.tar.gz \
&& tar -xzf lit-macos.tar.gz \
&& chmod +x lit \
&& (xattr -d com.apple.quarantine lit 2>/dev/null || true) \
&& sudo mkdir -p /usr/local/bin \
&& sudo mv lit /usr/local/bin/ \
&& rm lit-macos.tar.gz
```

### 🪟 Windows [Download](https://github.com/LIT-Tools/lit/releases/latest/download/lit-windows.zip)

```bash
irm https://github.com/LIT-Tools/lit/releases/latest/download/lit-windows.zip -OutFile lit-windows.zip
Expand-Archive -Path lit-windows.zip -DestinationPath . -Force
$p = "$HOME\lit"
New-Item -Path $p -ItemType Directory -Force | Out-Null
Move-Item -Path .\lit.exe -Destination $p -Force
$curPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
if ($curPath -notmatch "([\W;]|^)$([regex]::Escape($p))([\W;]|$)") {
    $env:PATH += ";$p"
    [Environment]::SetEnvironmentVariable('PATH', "$curPath$((';','')[$curPath -eq ''])$p", 'User')
}
rm lit-windows.zip
```

## 🚀 Основные команды

### Добавление записи
```bash
lit add <код_задачи> <время> "<сообщение>" [опции]

# Поддерживаемые форматы времени:
# 1h (1 час) | 30m (30 минут) | 1d (8 часов) | 1h 15m | 4 (4 часа)

# Примеры:
lit add TASK-1752 4 "Убрал из меню ссылку О компании"
lit add TASK-15 "1h 30m" "Исправление крэша" -d 25.12.2023 -t 10:00
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
# lit>
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
editor = nano # C:\Program Files\Notepad++\notepad++.exe

[jira]
login = user
pass = password
url = https://jira.com
days = 30

[gitlab]
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

1. Установите системные зависимости
```bash
# Для Debian/Ubuntu:
sudo apt-get update && sudo apt-get install -y \
    python3 python3-pip python3-venv git curl \
    build-essential libssl-dev zlib1g-dev

# Для Fedora/RHEL:
sudo dnf install -y python3 python3-pip python3-virtualenv git curl \
    gcc openssl-devel bzip2-devel libffi-devel zlib-devel
```

2. Установите Poetry
```bash
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

3. Установите pyenv (опционально, для управления версиями Python)
```bash
curl https://pyenv.run | bash

# Добавьте в ~/.bashrc:
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Установите нужную версию Python (пример):
pyenv install 3.12
pyenv global 3.12
```

4. Клонируйте репозиторий и установите зависимости
```bash
git clone https://github.com/LIT-Tools/lit.git
cd lit
poetry install
poetry shell  # или source .venv/bin/activate
```

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
coverage run --branch -m unittest discover
```
```bash
coverage report -m
```
```bash
coverage json -o coverage.json    
radon cc . -j -O cc.json   
python calc_crap.py
```

3. Откройте отчёт:

Windows
```bash
coverage html; Start-Process "htmlcov/index.html"
```
Linux / Mac
```bash
coverage html && open htmlcov/index.html
```

## 🔮 Планы развития

- [ ] Исправить подсказки ключей для команды `add`, убрать ложные срабатывания
- [x] Настроить сборку бинарника
- [x] Опубликовать в интернете для установки
- [x] Настроить версионирование
- [ ] Добавить проверку свежей версии и обновление
- [ ] Рефакторинг дублирующего кода
- [ ] Рефакторинг архитектуры под классический питонячий формат 
- [x] Повысить покрытие тестами 80+%
- [ ] Рефакторинг тестов
- [x] Понизить версию питона 
- [ ] Добавить мульти профили что бы подключаться к разным контурам

### 🤔 Возможное функции, но под вопросом:

- Настройка конфигурации из консоли 
`lit config` показывает конфиг
`lit config add <key> <value>` добавляет запись 

- В кофиге есть поле `start_time` с непустым значением и пользователь не предал значение через ключ -h то используем start_time как начальное время лога. Это защита если спец будет вносить логи поздно ночью

- Предупреждение если не была произведение конфигурация, файлй `~/.lit/.litconfig` нет.  

- Сохронять историю команд в интерактивном режиме

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
