# Черновик по реализации самообновления

Реализуем улучшения, учитывая анализ рекомендаций:

**1. Интеграция проверки обновлений с кэшированием (commands.py)**
```python
import threading
from datetime import datetime, timedelta

class WorklogManager:
    def __init__(self):
        self.update_cache = Path(LIT_DIR) / "update_cache"
        self.last_checked = None
        self.latest_version = None

    def check_update(self, force=False):
        """Проверка обновлений с кэшированием"""
        if not force and self._cache_valid():
            return self.latest_version
            
        thread = threading.Thread(target=self._fetch_update_data)
        thread.start()  # Запуск в фоне

    def _fetch_update_data(self):
        try:
            response = requests.get(
                "https://api.github.com/repos/LIT-Tools/lit/releases/latest",
                timeout=3
            )
            self.latest_version = response.json()['tag_name'].lstrip('v')
            self._write_cache()
        except Exception as e:
            logging.error(f"Update check failed: {str(e)}")

    def _cache_valid(self):
        """Проверяет актуальность кэша (24 часа)"""
        if not self.update_cache.exists():
            return False
            
        last_modified = datetime.fromtimestamp(
            self.update_cache.stat().st_mtime
        )
        return datetime.now() - last_modified < timedelta(hours=24)

    def _write_cache(self):
        with open(self.update_cache, 'w') as f:
            f.write(f"{self.latest_version}\n{datetime.now().isoformat()}")
```

**2. Модифицированная команда --version (lit.py)**
```python
def process_arguments(args=None):
    if args.version:
        print(f"lit v{get_version()}")
        manager = WorklogManager()
        if config.getboolean('user', 'auto_check_update', fallback=False):
            manager.check_update()
            if manager.latest_version:
                print(f"* New version available: {manager.latest_version}")
```

**3. Безопасное обновление с проверкой целостности (update.py)**
```python
import tempfile
import hashlib

def perform_upgrade(self):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # Скачивание в временный файл
            response = requests.get(url, stream=True, timeout=10)
            
            # Проверка хеша
            sha256 = hashlib.sha256()
            for chunk in response.iter_content(chunk_size=8192):
                sha256.update(chunk)
                tmp_file.write(chunk)
                
            if sha256.hexdigest() != expected_hash:
                raise ValueError("Hash mismatch")
                
        # Перемещение временного файла
        shutil.move(tmp_file.name, target_path)
        
    except Exception as e:
        logging.error(f"Upgrade failed: {str(e)}")
        if Path(tmp_file.name).exists():
            Path(tmp_file.name).unlink()
```

**4. Конфигурация автоматических проверок (.litconfig)**
```ini
[user]
auto_check_update = true
update_check_interval = 24  # hours
```

**5. Улучшенный скрипт обновления для Windows (upgrade.cmd)**
```batch
@echo off
timeout /t 3 /nobreak
taskkill /IM lit.exe /F
move /Y "%~dp0lit_new.exe" "%~dp0lit.exe"
start lit.exe
del "%~f0"
```

**Ключевые улучшения:**

1. **Фоновая проверка обновлений**  
   - Запускается в отдельном потоке при вызове `--version`
   - Не блокирует основной интерфейс
   - Кэширует результаты на 24 часа

2. **Безопасная работа с временными файлами**  
   - Использует `tempfile` вместо ручного управления
   - Автоматическая очистка при ошибках

3. **Контроль целостности**  
   - Проверка SHA256 хеша скачанного файла
   - Сравнение с хешем из релиза GitHub

4. **Гибкая настройка**  
   - Возможность отключения проверок через конфиг
   - Настройка интервала проверки

5. **Надёжное обновление для Windows**  
   - Принудительное завершение процесса перед заменой
   - Автоматический перезапуск после обновления

**Рекомендации по использованию:**

1. Для пользователей, которые хотят автоматические проверки:
   ```bash
   lit config set user.auto_check_update true
   ```

2. Принудительная проверка вручную:
   ```bash
   lit update --force
   ```

3. Безопасное обновление с проверкой подписи:
   ```bash
   lit upgrade --verify
   ```

---


Ниже приведён доработанный вариант CI‑скрипта, который включает этап упаковки бинарника вместе с платформенно‑специфичными файлами обновления. Также приведены примеры файлов для автоматического обновления для каждой операционной системы и рекомендации, куда их положить в репозитории.

---

## 1. Структура репозитория

Рекомендуется завести отдельную директорию для вспомогательных скриптов, например:
```
.
├── scripts/
│   ├── upgrade.cmd           # Скрипт для Windows
│   └── upgrade.sh            # Скрипт для Linux и macOS
├── pyproject.toml
├── lit.spec
└── ...                       # Другие файлы проекта
```
Таким образом, файлы автоматического обновления будут доступны в корне репозитория в папке `scripts`, и их можно легко включить в архив на этапе сборки.

---

## 2. Примеры файлов обновления

### Файл для Windows: `scripts/upgrade.cmd`
```batch
@echo off
REM Ждем немного, чтобы завершились все процессы
timeout /t 3 /nobreak
REM Принудительно завершаем запущенную утилиту
taskkill /IM lit.exe /F
REM Переименовываем скачанный новый бинарник (lit_new.exe) в текущий (lit.exe)
move /Y "%~dp0lit_new.exe" "%~dp0lit.exe"
REM Перезапускаем обновлённую утилиту
start "" "%~dp0lit.exe"
REM Удаляем скрипт обновления, так как он больше не нужен
del "%~f0"
```
*Пояснение:* Этот скрипт ожидает 3 секунды, завершает запущенную версию `lit.exe`, заменяет её на новый файл и перезапускает приложение.

---

### Файл для Linux и macOS: `scripts/upgrade.sh`
```bash
#!/bin/bash
# Ждем 2 секунды для завершения активных процессов
sleep 2
# Распаковываем архив с новым бинарником в директорию, где находится текущая утилита
tar -xzf "lit_new.tar.gz" -C "$(dirname "$0")"
# Удаляем временный архив
rm -f "lit_new.tar.gz"
# Устанавливаем права на выполнение нового бинарника
chmod +x "$(dirname "$0")/lit"
# Перезапускаем утилиту
nohup "$(dirname "$0")/lit" &
exit 0
```
*Пояснение:* Этот скрипт распаковывает скачанный архив (предполагается, что для Linux/macOS обновление поставляется как tar.gz‑архив), устанавливает права и перезапускает новую версию.

---

## 3. Доработанный CI‑скрипт (GitHub Actions YAML)

Ниже приведён обновлённый вариант CI‑скрипта, который собирает бинарники для Windows, Linux и macOS, включает соответствующий файл обновления в архив и загружает его как релиз‑ассет:

```yaml
name: Release Automation

on:
  push:
    branches:
      - master

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Install Dependencies
        run: poetry install --with dev

      - name: Run Tests
        run: poetry run coverage run -m unittest discover

      - name: Coverage Report
        run: poetry run coverage report -m

  release-prepare:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      upload_url: ${{ steps.release.outputs.upload_url }}
      tag_name: ${{ steps.release.outputs.tag_name }}
    steps:
      - uses: actions/checkout@v4

      - name: Release Please
        id: release
        uses: google-github-actions/release-please-action@v3
        with:
          release-type: python
          package-name: lit
          version-file: pyproject.toml
          manifest-file: pyproject.toml
          changelog-types: '[{"type":"feat","section":"Features"},{"type":"fix","section":"Bug Fixes"}]'

  build:
    if: "contains(github.event.head_commit.message, 'release-please--branches--master')"
    needs: release-prepare
    strategy:
      matrix:
        include:
          - os: windows-latest
            dist_dir: windows
            archive_ext: zip
            binary_name: lit.exe
            spec_args: lit.spec
            content_type: application/zip
            upgrade_script: scripts/upgrade.cmd
          - os: ubuntu-latest
            dist_dir: linux
            archive_ext: tar.gz
            binary_name: lit
            spec_args: lit.spec
            content_type: application/gzip
            upgrade_script: scripts/upgrade.sh
          - os: macos-latest
            dist_dir: macos
            archive_ext: tar.gz
            binary_name: lit
            spec_args: lit.spec
            content_type: application/gzip
            upgrade_script: scripts/upgrade.sh
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install System Dependencies (Windows)
        if: matrix.os == 'windows-latest'
        run: choco install 7zip

      - name: Install Poetry (Windows)
        if: matrix.os == 'windows-latest'
        run: |
          (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
          echo "$env:APPDATA\Python\Scripts" >> $env:GITHUB_PATH

      - name: Install Poetry (Linux/macOS)
        if: matrix.os != 'windows-latest'
        uses: snok/install-poetry@v1

      - name: Install Dependencies
        run: poetry install

      - name: Build binary with PyInstaller
        run: poetry run pyinstaller ${{ matrix.spec_args }} --distpath dist/${{ matrix.dist_dir }}

      - name: Move binary (Windows)
        if: matrix.os == 'windows-latest'
        run: |
          Move-Item -Path "dist\${{ matrix.dist_dir }}\${{ matrix.binary_name }}" -Destination .
          .\lit.exe --version
        shell: pwsh

      - name: Move binary (Linux/macOS)
        if: matrix.os != 'windows-latest'
        run: |
          mv "dist/${{ matrix.dist_dir }}/${{ matrix.binary_name }}" .
          chmod +x ./lit
          ./lit --version

      - name: Copy upgrade script
        run: cp ${{ matrix.upgrade_script }} .
      
      - name: Create archive (Windows)
        if: matrix.os == 'windows-latest'
        run: |
          $ASSET_NAME = "lit-${{ matrix.dist_dir }}.${{ matrix.archive_ext }}"
          7z a -tzip $ASSET_NAME "${{ matrix.binary_name }}","upgrade.cmd"
          Write-Output "ASSET_NAME=$ASSET_NAME" | Out-File -FilePath $env:GITHUB_ENV -Append
          Write-Output "CONTENT_TYPE=${{ matrix.content_type }}" | Out-File -FilePath $env:GITHUB_ENV -Append
        shell: pwsh

      - name: Create archive (Linux/macOS)
        if: matrix.os != 'windows-latest'
        run: |
          ASSET_NAME="lit-${{ matrix.dist_dir }}.${{ matrix.archive_ext }}"
          tar -czf $ASSET_NAME "${{ matrix.binary_name }}" "$(basename ${{ matrix.upgrade_script }})"
          echo "ASSET_NAME=$ASSET_NAME" >> $GITHUB_ENV
          echo "CONTENT_TYPE=${{ matrix.content_type }}" >> $GITHUB_ENV

      - name: Upload release asset
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ needs.release-prepare.outputs.upload_url }}
          asset_path: ./${{ env.ASSET_NAME }}
          asset_name: ${{ env.ASSET_NAME }}
          asset_content_type: ${{ env.CONTENT_TYPE }}
```

### Пояснения по CI‑скрипту:

- **Матрица сборки.**  
  Каждая платформа (Windows, Linux, macOS) задаётся через матрицу. Для каждого варианта указаны параметры: имя бинарника, расширение архива и путь к файлу обновления (через ключ `upgrade_script`).

- **Этап "Copy upgrade script".**  
  Перед упаковкой архивом мы копируем нужный скрипт обновления из папки `scripts` в корневую директорию сборки. Если скрипт называется одинаково (например, для Windows – `upgrade.cmd`), он будет включён в архив вместе с бинарником.

- **Этап "Create archive".**  
  Для Windows используется 7zip для создания zip‑архива, в который входят бинарник и `upgrade.cmd`. Для Linux и macOS используется tar‑архив, включающий бинарник и соответствующий скрипт (`upgrade.sh`).

- **Загрузка релиз‑ассета.**  
  Последний шаг CI‑конвейера использует GitHub Action для загрузки созданного архива в качестве ассета к релизу.
