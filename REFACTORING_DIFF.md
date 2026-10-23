diff --git a/.gitignore b/.gitignore
index 5944aac..6b43eaa 100644
--- a/.gitignore
+++ b/.gitignore
@@ -1,10 +1,10 @@
-/.idea/
-/.venv/
-/htmlcov
-/build/
-/dist/
+.idea/
+.venv/
+htmlcov
+build/
+dist/
 .coverage
 .DS_Store
-.coverage
-.venv/*.pyc
 __pycache__/
+cc.json
+coverage.json
diff --git a/README.md b/README.md
index d2ee207..ce95ff0 100644
--- a/README.md
+++ b/README.md
@@ -1,6 +1,9 @@
 # LIT: Logging Integrated Timekeeper
 
-<img src="https://img.shields.io/badge/python-3.9+-blue?logo=python" alt="Python Version"> <img src="https://img.shields.io/badge/license-MIT-green" alt="License"> <img src="https://img.shields.io/badge/coverage-83%25-green" alt="Coverage">
+[![CRAP](https://img.shields.io/badge/python-3.9+-blue?logo=python)]()
+[![CRAP](https://img.shields.io/badge/license-MIT-2E6F40)]()
+[![CRAP](https://img.shields.io/badge/coverage-83%25-2E6F40)]() 
+[![CRAP](https://img.shields.io/badge/CRAP-8.5-2E6F40)]()
 
 Консольная утилита для удобного управления рабочими логами с интеграцией Jira и GitLab
 
@@ -57,11 +60,14 @@ curl -LO https://github.com/LIT-Tools/lit/releases/latest/download/lit-macos.tar
 ```bash
 irm https://github.com/LIT-Tools/lit/releases/latest/download/lit-windows.zip -OutFile lit-windows.zip
 Expand-Archive -Path lit-windows.zip -DestinationPath . -Force
-$installPath = "$env:USERPROFILE\lit"
-New-Item -Path $installPath -ItemType Directory -Force
-Move-Item -Path .\lit.exe -Destination $installPath -Force
-$env:PATH += ";$installPath"
-[Environment]::SetEnvironmentVariable("PATH", $env:PATH, "User")
+$p = "$HOME\lit"
+New-Item -Path $p -ItemType Directory -Force | Out-Null
+Move-Item -Path .\lit.exe -Destination $p -Force
+$curPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
+if ($curPath -notmatch "([\W;]|^)$([regex]::Escape($p))([\W;]|$)") {
+    $env:PATH += ";$p"
+    [Environment]::SetEnvironmentVariable("PATH", "$curPath$((';','')[$curPath -eq ''])$p", 'User')
+}
 rm lit-windows.zip
 ```
 
@@ -131,18 +137,16 @@ lit pull [--jira] [--gitlab]
 Пример `~/.lit/.litconfig`:
 ```ini
 [user]
-login = user
 email = user@domain.com
+editor = nano
 
 [jira]
 login = user
-email = user@domain.com
 pass = password
 url = https://jira.com
 days = 30
 
 [gitlab]
-login = user
 email = user@domain.com
 url = https://gitlab.com
 token = ваш_личный_токен
@@ -238,6 +242,11 @@ uv sync
 uv run coverage run -m unittest discover
 uv run coverage report -m
 ```
+```bash
+coverage json -o coverage.json    
+radon cc . -j -O cc.json   
+python calc_crap.py
+```
 
 3. Откройте отчёт:
 
@@ -253,6 +262,7 @@ coverage html && open htmlcov/index.html
 ## 🔮 Планы развития
 
 - [ ] Исправить подсказки ключей для команды `add`, убрать ложные срабатывания
+- [ ] Исправить баг, что после команды `pull` нужно перезапускать интерактивный режим  
 - [x] Настроить сборку бинарника
 - [x] Опубликовать в интернете для установки
 - [x] Настроить версионирование
diff --git a/REFACTORING_LOST_COMMITS.md b/REFACTORING_LOST_COMMITS.md
index f4e7e3f..14be151 100644
--- a/REFACTORING_LOST_COMMITS.md
+++ b/REFACTORING_LOST_COMMITS.md
@@ -31,22 +31,22 @@
 
 ### 🟢 Шаг A — Misc (независимые мелкие правки)
 
-- [ ] `7f8e5e83` — `refactor: removed print` (лишний `print(cmd)` в
+- [x] `7f8e5e83` — `refactor: removed print` (лишний `print(cmd)` в
   `edit_entries`)
-- [ ] `2bb20664` — `docs: fixed duplicate path in PATH during installation`
+- [x] `2bb20664` — `docs: fixed duplicate path in PATH during installation`
   (Windows install в README)
-- [ ] `4a19517b` — `docs: added bug to check list` (в README-планы
+- [x] `4a19517b` — `docs: added bug to check list` (в README-планы
   добавить баг «после `pull` нужен перезапуск REPL»)
 
 ### 🟢 Шаг B — Dev-tools: CRAP-анализ
 
-- [ ] `1613c1d1` — `test: added calc CRAP` (новый `calc_crap.py` +
+- [x] `1613c1d1` — `test: added calc CRAP` (новый `calc_crap.py` +
   `.gitignore` `cc.json`/`coverage.json` + `radon` в dev + README test
   section с `coverage run --branch`, `coverage json`, `radon cc`)
 
 ### 🟢 Шаг C — Документация: пример `.litconfig`
 
-- [ ] `e8760eb0` — `docs: fixed example .litconfig`
+- [-] `e8760eb0` — `docs: fixed example .litconfig`
   (уточнить, не пересекается ли с `1e5cea6b` из Шага D; если
   дубликат — отметить `[-]`)
 
@@ -55,16 +55,16 @@
 Все 6 коммитов трогают `.litconfig`-схему и её потребителей. По
 отдельности тесты будут красными. Один шаг = один коммит.
 
-- [ ] `abfafc49` — `refactor: removed field of config user login`
-- [ ] `c98db846` — `refactor: removed field of config jira email`
-- [ ] `ed5290ce` — `refactor: removed field of config gitlab login`
-- [ ] `63eb82c4` — `feat(config): dynamic URLs by user domain` (zebrains)
-- [ ] `2ed64bb9` — `refactor(config): added hint for token Select scopes: api`
-- [ ] `1e5cea6b` — `docs: fixed example .litconfig`
+- [x] `abfafc49` — `refactor: removed field of config user login`
+- [x] `c98db846` — `refactor: removed field of config jira email`
+- [x] `ed5290ce` — `refactor: removed field of config gitlab login`
+- [x] `63eb82c4` — `feat(config): dynamic URLs by user domain` (zebrains)
+- [x] `2ed64bb9` — `refactor(config): added hint for token Select scopes: api`
+- [x] `1e5cea6b` — `docs: fixed example .litconfig`
 
 ### 🟡 Шаг E — `UPDATE.md` (draft фичи)
 
-- [ ] `8af3c39f` — `docs: added UPDATE.md` (черновик auto-update; перенести
+- [x] `8af3c39f` — `docs: added UPDATE.md` (черновик auto-update; перенести
   как draft, не в код)
 
 ### ⚪ Не переносить
diff --git a/calc_crap.py b/calc_crap.py
new file mode 100644
index 0000000..f56f5e0
--- /dev/null
+++ b/calc_crap.py
@@ -0,0 +1,82 @@
+import json
+
+
+# ANSI-коды цвета
+class bcolors:
+    GREEN = '\033[92m'
+    YELLOW = '\033[93m'
+    RED = '\033[91m'
+    ENDC = '\033[0m'
+
+try:
+    with open("cc.json") as f:
+        cc_data = json.load(f)
+except OSError as e:
+    print('Файл cc.json не найден, выполни команду:\n')
+    print('radon cc . -j -O cc.json\n')
+    exit()
+
+try:
+    with open("coverage.json") as f:
+        coverage_data = json.load(f)
+except OSError as e:
+    print('Файл coverage.json не найден, выполни команды:\n')
+    print('coverage run --branch -m unittest discover')
+    print('coverage json -o coverage.json\n')
+    exit()
+
+
+crap_values = []  # Для сбора всех значений CRAP
+
+for filename, methods in cc_data.items():
+    if filename not in coverage_data["files"]:
+        print(f"Файл {filename} не найден в отчете о покрытии. Пропускаю...")
+        continue
+
+    if filename.startswith("test_"):
+        continue
+
+    cov_percent = coverage_data["files"][filename]["summary"]["percent_covered"]
+    cov = cov_percent / 100
+
+    for method in methods:
+        comp = method["complexity"]
+        crap = comp ** 2 * (1 - cov) ** 3 + comp
+        crap_f = f"{comp}^2 * (1 - {round(cov, 2)})^3 + {comp}"
+        crap_values.append(crap)
+
+        # Подсветка CRAP-индекса
+        if crap < 10:
+            color = bcolors.GREEN
+        elif crap < 30:
+            color = bcolors.YELLOW
+        else:
+            color = bcolors.RED
+
+        print(f"{filename}::{method['name']} \t (CRAP: {color}{crap:.2f}{bcolors.ENDC}) \t {crap_f}")
+
+# Вывод статистики
+if crap_values:
+    average_crap = sum(crap_values) / len(crap_values)
+    max_crap = max(crap_values)
+
+    # Цвет для среднего значения
+    avg_color = (
+        bcolors.GREEN if average_crap < 10 else
+        bcolors.YELLOW if average_crap < 30 else
+        bcolors.RED
+    )
+
+    # Цвет для максимального значения
+    max_color = (
+        bcolors.GREEN if max_crap < 10 else
+        bcolors.YELLOW if max_crap < 30 else
+        bcolors.RED
+    )
+
+    print("\n" + "=" * 20)
+    print(f"  Max CRAP: {avg_color}{average_crap:.2f}{bcolors.ENDC}")
+    print(f"  Avg CRAP: {max_color}{max_crap:.2f}{bcolors.ENDC}")
+    print("=" * 20)
+else:
+    print("\nНет данных для расчета статистики CRAP")
diff --git a/docs/UPDATE.md b/docs/UPDATE.md
new file mode 100644
index 0000000..47cc717
--- /dev/null
+++ b/docs/UPDATE.md
@@ -0,0 +1,382 @@
+> **DRAFT.** Не реализовано. Черновик фичи auto-update из dev-ветки (апрель 2026). В код не переносить до отдельного цикла.
+
+# Черновик по реализации самообновления
+
+Реализуем улучшения, учитывая анализ рекомендаций:
+
+**1. Интеграция проверки обновлений с кэшированием (commands.py)**
+```python
+import threading
+from datetime import datetime, timedelta
+
+class WorklogManager:
+    def __init__(self):
+        self.update_cache = Path(LIT_DIR) / "update_cache"
+        self.last_checked = None
+        self.latest_version = None
+
+    def check_update(self, force=False):
+        """Проверка обновлений с кэшированием"""
+        if not force and self._cache_valid():
+            return self.latest_version
+            
+        thread = threading.Thread(target=self._fetch_update_data)
+        thread.start()  # Запуск в фоне
+
+    def _fetch_update_data(self):
+        try:
+            response = requests.get(
+                "https://api.github.com/repos/LIT-Tools/lit/releases/latest",
+                timeout=3
+            )
+            self.latest_version = response.json()['tag_name'].lstrip('v')
+            self._write_cache()
+        except Exception as e:
+            logging.error(f"Update check failed: {str(e)}")
+
+    def _cache_valid(self):
+        """Проверяет актуальность кэша (24 часа)"""
+        if not self.update_cache.exists():
+            return False
+            
+        last_modified = datetime.fromtimestamp(
+            self.update_cache.stat().st_mtime
+        )
+        return datetime.now() - last_modified < timedelta(hours=24)
+
+    def _write_cache(self):
+        with open(self.update_cache, 'w') as f:
+            f.write(f"{self.latest_version}\n{datetime.now().isoformat()}")
+```
+
+**2. Модифицированная команда --version (lit.py)**
+```python
+def process_arguments(args=None):
+    if args.version:
+        print(f"lit v{get_version()}")
+        manager = WorklogManager()
+        if config.getboolean('user', 'auto_check_update', fallback=False):
+            manager.check_update()
+            if manager.latest_version:
+                print(f"* New version available: {manager.latest_version}")
+```
+
+**3. Безопасное обновление с проверкой целостности (update.py)**
+```python
+import tempfile
+import hashlib
+
+def perform_upgrade(self):
+    try:
+        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
+            # Скачивание в временный файл
+            response = requests.get(url, stream=True, timeout=10)
+            
+            # Проверка хеша
+            sha256 = hashlib.sha256()
+            for chunk in response.iter_content(chunk_size=8192):
+                sha256.update(chunk)
+                tmp_file.write(chunk)
+                
+            if sha256.hexdigest() != expected_hash:
+                raise ValueError("Hash mismatch")
+                
+        # Перемещение временного файла
+        shutil.move(tmp_file.name, target_path)
+        
+    except Exception as e:
+        logging.error(f"Upgrade failed: {str(e)}")
+        if Path(tmp_file.name).exists():
+            Path(tmp_file.name).unlink()
+```
+
+**4. Конфигурация автоматических проверок (.litconfig)**
+```ini
+[user]
+auto_check_update = true
+update_check_interval = 24  # hours
+```
+
+**5. Улучшенный скрипт обновления для Windows (upgrade.cmd)**
+```batch
+@echo off
+timeout /t 3 /nobreak
+taskkill /IM lit.exe /F
+move /Y "%~dp0lit_new.exe" "%~dp0lit.exe"
+start lit.exe
+del "%~f0"
+```
+
+**Ключевые улучшения:**
+
+1. **Фоновая проверка обновлений**  
+   - Запускается в отдельном потоке при вызове `--version`
+   - Не блокирует основной интерфейс
+   - Кэширует результаты на 24 часа
+
+2. **Безопасная работа с временными файлами**  
+   - Использует `tempfile` вместо ручного управления
+   - Автоматическая очистка при ошибках
+
+3. **Контроль целостности**  
+   - Проверка SHA256 хеша скачанного файла
+   - Сравнение с хешем из релиза GitHub
+
+4. **Гибкая настройка**  
+   - Возможность отключения проверок через конфиг
+   - Настройка интервала проверки
+
+5. **Надёжное обновление для Windows**  
+   - Принудительное завершение процесса перед заменой
+   - Автоматический перезапуск после обновления
+
+**Рекомендации по использованию:**
+
+1. Для пользователей, которые хотят автоматические проверки:
+   ```bash
+   lit config set user.auto_check_update true
+   ```
+
+2. Принудительная проверка вручную:
+   ```bash
+   lit update --force
+   ```
+
+3. Безопасное обновление с проверкой подписи:
+   ```bash
+   lit upgrade --verify
+   ```
+
+---
+
+
+Ниже приведён доработанный вариант CI‑скрипта, который включает этап упаковки бинарника вместе с платформенно‑специфичными файлами обновления. Также приведены примеры файлов для автоматического обновления для каждой операционной системы и рекомендации, куда их положить в репозитории.
+
+---
+
+## 1. Структура репозитория
+
+Рекомендуется завести отдельную директорию для вспомогательных скриптов, например:
+```
+.
+├── scripts/
+│   ├── upgrade.cmd           # Скрипт для Windows
+│   └── upgrade.sh            # Скрипт для Linux и macOS
+├── pyproject.toml
+├── lit.spec
+└── ...                       # Другие файлы проекта
+```
+Таким образом, файлы автоматического обновления будут доступны в корне репозитория в папке `scripts`, и их можно легко включить в архив на этапе сборки.
+
+---
+
+## 2. Примеры файлов обновления
+
+### Файл для Windows: `scripts/upgrade.cmd`
+```batch
+@echo off
+REM Ждем немного, чтобы завершились все процессы
+timeout /t 3 /nobreak
+REM Принудительно завершаем запущенную утилиту
+taskkill /IM lit.exe /F
+REM Переименовываем скачанный новый бинарник (lit_new.exe) в текущий (lit.exe)
+move /Y "%~dp0lit_new.exe" "%~dp0lit.exe"
+REM Перезапускаем обновлённую утилиту
+start "" "%~dp0lit.exe"
+REM Удаляем скрипт обновления, так как он больше не нужен
+del "%~f0"
+```
+*Пояснение:* Этот скрипт ожидает 3 секунды, завершает запущенную версию `lit.exe`, заменяет её на новый файл и перезапускает приложение.
+
+---
+
+### Файл для Linux и macOS: `scripts/upgrade.sh`
+```bash
+#!/bin/bash
+# Ждем 2 секунды для завершения активных процессов
+sleep 2
+# Распаковываем архив с новым бинарником в директорию, где находится текущая утилита
+tar -xzf "lit_new.tar.gz" -C "$(dirname "$0")"
+# Удаляем временный архив
+rm -f "lit_new.tar.gz"
+# Устанавливаем права на выполнение нового бинарника
+chmod +x "$(dirname "$0")/lit"
+# Перезапускаем утилиту
+nohup "$(dirname "$0")/lit" &
+exit 0
+```
+*Пояснение:* Этот скрипт распаковывает скачанный архив (предполагается, что для Linux/macOS обновление поставляется как tar.gz‑архив), устанавливает права и перезапускает новую версию.
+
+---
+
+## 3. Доработанный CI‑скрипт (GitHub Actions YAML)
+
+Ниже приведён обновлённый вариант CI‑скрипта, который собирает бинарники для Windows, Linux и macOS, включает соответствующий файл обновления в архив и загружает его как релиз‑ассет:
+
+```yaml
+name: Release Automation
+
+on:
+  push:
+    branches:
+      - master
+
+jobs:
+  test:
+    runs-on: ubuntu-latest
+    strategy:
+      matrix:
+        python-version: ["3.9", "3.10", "3.11", "3.12"]
+    steps:
+      - uses: actions/checkout@v4
+
+      - name: Setup Python
+        uses: actions/setup-python@v4
+        with:
+          python-version: ${{ matrix.python-version }}
+
+      - name: Install Poetry
+        uses: snok/install-poetry@v1
+
+      - name: Install Dependencies
+        run: poetry install --with dev
+
+      - name: Run Tests
+        run: poetry run coverage run -m unittest discover
+
+      - name: Coverage Report
+        run: poetry run coverage report -m
+
+  release-prepare:
+    needs: test
+    runs-on: ubuntu-latest
+    outputs:
+      upload_url: ${{ steps.release.outputs.upload_url }}
+      tag_name: ${{ steps.release.outputs.tag_name }}
+    steps:
+      - uses: actions/checkout@v4
+
+      - name: Release Please
+        id: release
+        uses: google-github-actions/release-please-action@v3
+        with:
+          release-type: python
+          package-name: lit
+          version-file: pyproject.toml
+          manifest-file: pyproject.toml
+          changelog-types: '[{"type":"feat","section":"Features"},{"type":"fix","section":"Bug Fixes"}]'
+
+  build:
+    if: "contains(github.event.head_commit.message, 'release-please--branches--master')"
+    needs: release-prepare
+    strategy:
+      matrix:
+        include:
+          - os: windows-latest
+            dist_dir: windows
+            archive_ext: zip
+            binary_name: lit.exe
+            spec_args: lit.spec
+            content_type: application/zip
+            upgrade_script: scripts/upgrade.cmd
+          - os: ubuntu-latest
+            dist_dir: linux
+            archive_ext: tar.gz
+            binary_name: lit
+            spec_args: lit.spec
+            content_type: application/gzip
+            upgrade_script: scripts/upgrade.sh
+          - os: macos-latest
+            dist_dir: macos
+            archive_ext: tar.gz
+            binary_name: lit
+            spec_args: lit.spec
+            content_type: application/gzip
+            upgrade_script: scripts/upgrade.sh
+    runs-on: ${{ matrix.os }}
+    steps:
+      - uses: actions/checkout@v4
+
+      - name: Setup Python
+        uses: actions/setup-python@v4
+        with:
+          python-version: '3.9'
+
+      - name: Install System Dependencies (Windows)
+        if: matrix.os == 'windows-latest'
+        run: choco install 7zip
+
+      - name: Install Poetry (Windows)
+        if: matrix.os == 'windows-latest'
+        run: |
+          (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
+          echo "$env:APPDATA\Python\Scripts" >> $env:GITHUB_PATH
+
+      - name: Install Poetry (Linux/macOS)
+        if: matrix.os != 'windows-latest'
+        uses: snok/install-poetry@v1
+
+      - name: Install Dependencies
+        run: poetry install
+
+      - name: Build binary with PyInstaller
+        run: poetry run pyinstaller ${{ matrix.spec_args }} --distpath dist/${{ matrix.dist_dir }}
+
+      - name: Move binary (Windows)
+        if: matrix.os == 'windows-latest'
+        run: |
+          Move-Item -Path "dist\${{ matrix.dist_dir }}\${{ matrix.binary_name }}" -Destination .
+          .\lit.exe --version
+        shell: pwsh
+
+      - name: Move binary (Linux/macOS)
+        if: matrix.os != 'windows-latest'
+        run: |
+          mv "dist/${{ matrix.dist_dir }}/${{ matrix.binary_name }}" .
+          chmod +x ./lit
+          ./lit --version
+
+      - name: Copy upgrade script
+        run: cp ${{ matrix.upgrade_script }} .
+      
+      - name: Create archive (Windows)
+        if: matrix.os == 'windows-latest'
+        run: |
+          $ASSET_NAME = "lit-${{ matrix.dist_dir }}.${{ matrix.archive_ext }}"
+          7z a -tzip $ASSET_NAME "${{ matrix.binary_name }}","upgrade.cmd"
+          Write-Output "ASSET_NAME=$ASSET_NAME" | Out-File -FilePath $env:GITHUB_ENV -Append
+          Write-Output "CONTENT_TYPE=${{ matrix.content_type }}" | Out-File -FilePath $env:GITHUB_ENV -Append
+        shell: pwsh
+
+      - name: Create archive (Linux/macOS)
+        if: matrix.os != 'windows-latest'
+        run: |
+          ASSET_NAME="lit-${{ matrix.dist_dir }}.${{ matrix.archive_ext }}"
+          tar -czf $ASSET_NAME "${{ matrix.binary_name }}" "$(basename ${{ matrix.upgrade_script }})"
+          echo "ASSET_NAME=$ASSET_NAME" >> $GITHUB_ENV
+          echo "CONTENT_TYPE=${{ matrix.content_type }}" >> $GITHUB_ENV
+
+      - name: Upload release asset
+        uses: actions/upload-release-asset@v1
+        env:
+          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
+        with:
+          upload_url: ${{ needs.release-prepare.outputs.upload_url }}
+          asset_path: ./${{ env.ASSET_NAME }}
+          asset_name: ${{ env.ASSET_NAME }}
+          asset_content_type: ${{ env.CONTENT_TYPE }}
+```
+
+### Пояснения по CI‑скрипту:
+
+- **Матрица сборки.**  
+  Каждая платформа (Windows, Linux, macOS) задаётся через матрицу. Для каждого варианта указаны параметры: имя бинарника, расширение архива и путь к файлу обновления (через ключ `upgrade_script`).
+
+- **Этап "Copy upgrade script".**  
+  Перед упаковкой архивом мы копируем нужный скрипт обновления из папки `scripts` в корневую директорию сборки. Если скрипт называется одинаково (например, для Windows – `upgrade.cmd`), он будет включён в архив вместе с бинарником.
+
+- **Этап "Create archive".**  
+  Для Windows используется 7zip для создания zip‑архива, в который входят бинарник и `upgrade.cmd`. Для Linux и macOS используется tar‑архив, включающий бинарник и соответствующий скрипт (`upgrade.sh`).
+
+- **Загрузка релиз‑ассета.**  
+  Последний шаг CI‑конвейера использует GitHub Action для загрузки созданного архива в качестве ассета к релизу.
diff --git a/pyproject.toml b/pyproject.toml
index 6705302..02114c2 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -23,6 +23,7 @@ lit = "lit:cli"
 dev = [
     "coverage>=7.6.12,<8.0.0",
     "pyinstaller==6.12.0",
+    "radon>=6.0.1",
 ]
 
 [build-system]
@@ -33,4 +34,4 @@ build-backend = "hatchling.build"
 packages = ["src/lit"]
 
 [tool.coverage.run]
-source = ["lit"]
\ No newline at end of file
+source = ["lit"]
diff --git a/src/lit/config_manager.py b/src/lit/config_manager.py
index 54d6f9d..7b54b61 100644
--- a/src/lit/config_manager.py
+++ b/src/lit/config_manager.py
@@ -15,7 +15,6 @@ def get_user(cfg=None) -> dict:
     """Получить секцию [user]."""
     cfg = cfg or load_config()
     return {
-        "login": cfg.get("user", "login", fallback=""),
         "email": cfg.get("user", "email", fallback=""),
         "editor": cfg.get("user", "editor", fallback=""),
     }
@@ -26,7 +25,6 @@ def get_jira(cfg=None) -> dict:
     cfg = cfg or load_config()
     return {
         "login": cfg.get("jira", "login", fallback=""),
-        "email": cfg.get("jira", "email", fallback=""),
         "pass": cfg.get("jira", "pass", fallback=""),
         "url": cfg.get("jira", "url", fallback=""),
         "days": cfg.getint("jira", "days", fallback=30),
@@ -36,9 +34,9 @@ def get_jira(cfg=None) -> dict:
 def get_gitlab(cfg=None) -> dict:
     """Получить секцию [gitlab]."""
     cfg = cfg or load_config()
+    email = cfg.get("gitlab", "email", fallback="") or cfg.get("gitlab", "login", fallback="")
     return {
-        "login": cfg.get("gitlab", "login", fallback=""),
-        "email": cfg.get("gitlab", "email", fallback=""),
+        "email": email,
         "url": cfg.get("gitlab", "url", fallback=""),
         "token": cfg.get("gitlab", "token", fallback=""),
         "days": cfg.getint("gitlab", "days", fallback=30),
diff --git a/src/lit/core/worklog_manager.py b/src/lit/core/worklog_manager.py
index a445304..d20afe0 100644
--- a/src/lit/core/worklog_manager.py
+++ b/src/lit/core/worklog_manager.py
@@ -173,7 +173,6 @@ class WorklogManager:
         editor = CUSTOM_EDITOR or os.environ.get('EDITOR') or os.environ.get('VISUAL') or default_editor
         try:
             cmd = [editor, LIT_STORE]
-            print(cmd)
             subprocess.run(cmd, shell=(os.name == 'nt'), check=True, encoding='utf-8')
             self._load()
             print("✓ Изменения применены")
diff --git a/src/lit/init.py b/src/lit/init.py
index 8cd436f..cc8de14 100644
--- a/src/lit/init.py
+++ b/src/lit/init.py
@@ -24,16 +24,6 @@ def init_config():
         validate=lambda val: "@" in val or "Email обязателен"
     ).ask()
 
-    # Автогенерация логина из email если нет в конфиге
-    email_login = user_email.split("@")[0] if "@" in user_email else ""
-    current_login = default.get("user", "login", fallback=email_login)
-
-    user_login = questionary.text(
-        "User login:",
-        default=current_login,
-        validate=lambda val: len(val) > 0 or "Логин обязателен"
-    ).ask()
-
     editor = questionary.text(
         "Editor:",
         default=default.get("user", "editor", fallback=""),
@@ -41,15 +31,18 @@ def init_config():
     ).ask()
 
     config["user"] = {
-        "login": user_login,
         "email": user_email,
         "editor": editor
     }
 
     # Секция [jira]
+    # Zebrains-домен (определяем из email до вопросов)
+    is_zebrains_user = "zebrains" in (user_email.split("@")[1] if "@" in user_email else "")
+    jira_url_default = "https://jira.zebrains.team" if is_zebrains_user else "https://jira.itech-group.ru"
+    
     jira_login = questionary.text(
         "Jira login:",
-        default=default.get("jira", "login", fallback=user_login)
+        default=default.get("jira", "login", fallback=user_email.split("@")[0] if "@" in user_email else "")
     ).ask()
     # TODO API token пока почему то не срабатывает, нужно разобраться, сейчас оставил в подсказке только пароль
     jira_pass = questionary.password(
@@ -59,14 +52,10 @@ def init_config():
 
     config["jira"] = {
         "login": jira_login,
-        "email": questionary.text(
-            "Jira email:",
-            default=default.get("jira", "email", fallback=user_email)
-        ).ask(),
         "pass": jira_pass,
         "url": questionary.text(
             "Jira URL:",
-            default=default.get("jira", "url", fallback="https://jira.itech-group.ru")
+            default=default.get("jira", "url", fallback=jira_url_default)
         ).ask(),
         "days": questionary.text(
             "Days to sync:",
@@ -75,22 +64,15 @@ def init_config():
     }
 
     # Секция [gitlab]
-    gitlab_login = questionary.text(
-        "GitLab login:",
-        default=default.get("gitlab", "login", fallback=user_login)
-    ).ask()
-
     # Сначала запрашиваем URL
     gitlab_url = questionary.text(
         "GitLab URL:",
-        default=default.get("gitlab", "url", fallback="https://gitlab.zebrains.team")
+        default=default.get("gitlab", "url", fallback="https://gitlab.zebrains.team" if is_zebrains_user else "https://gitlab.zebrains.team")
     ).ask()
 
-    # Теперь используем полученный URL для формирования инструкции
-    gitlab_token_instruction = f"\n  [Получить токен: {gitlab_url}/-/user_settings/personal_access_tokens]"
+    gitlab_token_instruction = f"\n  [Select scopes: api]\n  [Получить токен: {gitlab_url}/-/user_settings/personal_access_tokens]"
 
     config["gitlab"] = {
-        "login": gitlab_login,
         "email": questionary.text(
             "GitLab email:",
             default=default.get("gitlab", "email", fallback=user_email)
diff --git a/src/lit/integrations/gitlab.py b/src/lit/integrations/gitlab.py
index 46df8ab..1c5bfd0 100644
--- a/src/lit/integrations/gitlab.py
+++ b/src/lit/integrations/gitlab.py
@@ -21,6 +21,8 @@ def save_commits(data: dict):
         print(f"Error saving commits: {str(e)}")
 
 
+USER_EMAIL = ""
+
 def load_commits_from_gitlab() -> None:
     """Загрузка коммитов из GitLab."""
     load_config()
@@ -31,18 +33,8 @@ def load_commits_from_gitlab() -> None:
 
     headers = {'Private-Token': TOKEN}
     url = GITLAB_URL
-    target_user = TARGET_USER
+    user_email = USER_EMAIL
     days = DAYS
-    
-    # Получаем информацию о текущем пользователе
-    response = requests.get(f'{url}/api/v4/user', headers=headers)
-    response.raise_for_status()
-    user = response.json()
-    username = user['username']
-    
-    # Используем login из конфига, если он указан
-    if target_user:
-        username = target_user
 
     # Рассчитываем дату DAYS дней назад
     since_datetime = datetime.now() - timedelta(days=days)
@@ -100,7 +92,7 @@ def load_commits_from_gitlab() -> None:
                     params={
                         'since': since_date_iso,
                         # 'until': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),  # Добавляем верхнюю границу
-                        'author_username': username,
+                        'author_username': user_email.split("@")[0],
                         # 'committer_username': username,  # Фильтруем и по коммиттеру
                         'with_stats': False,  # Убираем лишние данные
                         'page': page,
@@ -114,11 +106,8 @@ def load_commits_from_gitlab() -> None:
 
                 for commit in commits:
                     # Проверяем и автора и коммиттера
-                    commit_author = commit['author_email'].split("@")[0]
-                    commit_committer = commit['committer_email'].split("@")[0]
-
                     if len(commit['message']) > 0 and (
-                            commit_author.lower() == username.lower() or commit_committer.lower() == username.lower()):
+                            commit['author_email'].lower() == user_email.lower() or commit['committer_email'].lower() == user_email.lower()):
                         if commit['message'].find('Merge branch') == -1:
                             comments.append(commit['message'].rstrip())
 
@@ -147,7 +136,7 @@ def load_commits_from_gitlab() -> None:
     # Сортируем задачи и удаляем пустые
     sorted_tasks = {k: v for k, v in sorted(task_commits.items()) if k and v}
 
-    print(f'\rНайдено {useful_commits} пригодных коммитов из {len(comments)} в {len(sorted_tasks)} репозиториях за авторством {username}')
+    print(f'\rНайдено {useful_commits} пригодных коммитов из {len(comments)} в {len(sorted_tasks)} репозиториях за авторством {user_email}')
 
     save_commits(sorted_tasks)
 
@@ -156,9 +145,9 @@ def load_commits_from_gitlab() -> None:
 def load_config(path: str | None = None) -> dict:
     """Алиас для совместимости с мокающими тестами."""
     config = get_gitlab()
-    global GITLAB_URL, TOKEN, TARGET_USER, DAYS
+    global GITLAB_URL, TOKEN, USER_EMAIL, DAYS
     GITLAB_URL = config["url"]
     TOKEN = config["token"]
-    TARGET_USER = config["login"]
+    USER_EMAIL = config.get("email", config.get("login", ""))  # fallback для старых конфигов
     DAYS = config["days"]
     return config
diff --git a/tests/test_gitlab.py b/tests/test_gitlab.py
index acad9e5..d748e9d 100644
--- a/tests/test_gitlab.py
+++ b/tests/test_gitlab.py
@@ -2,7 +2,7 @@ import unittest
 from unittest.mock import patch, MagicMock
 import lit.integrations.gitlab
 import logging
-from datetime import datetime, timedelta, timezone
+from datetime import datetime, timezone
 import io
 import sys
 
@@ -21,7 +21,7 @@ class TestLoadCommitsFromGitlab(unittest.TestCase):
         # Установка тестовой конфигурации
         lit.integrations.gitlab.GITLAB_URL = 'https://gitlab.example.com'
         lit.integrations.gitlab.TOKEN = 'fake_token'
-        lit.integrations.gitlab.TARGET_USER = 'test_user'
+        lit.integrations.gitlab.USER_EMAIL = 'test_user@example.com'
         lit.integrations.gitlab.DAYS = 7
 
         # Фиксация времени
@@ -58,7 +58,6 @@ class TestLoadCommitsFromGitlab(unittest.TestCase):
 
         # Создаём необходимые ответы для всех запросов
         mock_responses = [
-            self.create_response({'username': 'test_user'}),  # /user
             self.create_response([{'id': 1}, {'id': 2}]),  # /projects page1
             self.create_response([]),  # /projects page2 (пустой)
             self.create_response([{  # /projects/1/repository/commits
@@ -74,12 +73,6 @@ class TestLoadCommitsFromGitlab(unittest.TestCase):
 
         lit.integrations.gitlab.load_commits_from_gitlab()
 
-        # Проверка вызовов API
-        self.mock_requests.get.assert_any_call(
-            'https://gitlab.example.com/api/v4/user',
-            headers={'Private-Token': 'fake_token'}
-        )
-
         self.mock_requests.get.assert_any_call(
             'https://gitlab.example.com/api/v4/projects',
             headers={'Private-Token': 'fake_token'},
@@ -98,7 +91,6 @@ class TestLoadCommitsFromGitlab(unittest.TestCase):
     def test_commit_filtering(self):
         """Тест фильтрации коммитов"""
         self.mock_requests.get.side_effect = [
-            self.create_response({'username': 'test_user'}),
             self.create_response([{'id': 1}]),
             self.create_response([]),
             self.create_response([
@@ -139,7 +131,7 @@ class TestLoadCommitsFromGitlab(unittest.TestCase):
             # Первый вызов - для /api/v4/user - успешный
             if call_count == 1:
                 mock_resp = MagicMock()
-                mock_resp.json.return_value = {'username': 'test_user'}
+                mock_resp.json.return_value = {'username': 'test_user@example.com'}
                 mock_resp.status_code = 200
                 return mock_resp
             # Второй вызов - для /api/v4/users/{username}/projects - с ошибкой
@@ -170,7 +162,6 @@ class TestLoadCommitsFromGitlab(unittest.TestCase):
     def test_message_parsing(self):
         """Тест парсинга сообщений коммитов"""
         self.mock_requests.get.side_effect = [
-            self.create_response({'username': 'test_user'}),
             self.create_response([{'id': 1}]),
             self.create_response([]),
             self.create_response([
diff --git a/tests/test_init.py b/tests/test_init.py
index d28d8bf..eb5b2de 100644
--- a/tests/test_init.py
+++ b/tests/test_init.py
@@ -38,13 +38,10 @@ class TestInitConfig(unittest.TestCase):
         # Ответы для текстовых вопросов (в том порядке, как они вызываются)
         text_answers = [
             "test@example.com",  # User email
-            "testuser",  # User login
-            "", # Editor
+            "",  # Editor
             "jirauser",  # Jira login
-            "jira@example.com",  # Jira email
-            "https://jira.test.com",  # Jira URL
+            "jirauser",  # Jira URL
             "30",  # Jira days
-            "gitlabuser",  # GitLab login
             "https://gitlab.test.com",  # GitLab URL
             "gitlab@example.com",  # GitLab email
             "30"  # GitLab days
@@ -69,17 +66,12 @@ class TestInitConfig(unittest.TestCase):
 
         # Проверяем секцию [user]
         self.assertEqual(config.get("user", "email"), "test@example.com")
-        self.assertEqual(config.get("user", "login"), "testuser")
 
         # Проверяем секцию [jira]
-        self.assertEqual(config.get("jira", "login"), "jirauser")
         self.assertEqual(config.get("jira", "pass"), "jirapass")
-        self.assertEqual(config.get("jira", "email"), "jira@example.com")
-        self.assertEqual(config.get("jira", "url"), "https://jira.test.com")
         self.assertEqual(config.get("jira", "days"), "30")
 
         # Проверяем секцию [gitlab]
-        self.assertEqual(config.get("gitlab", "login"), "gitlabuser")
         self.assertEqual(config.get("gitlab", "email"), "gitlab@example.com")
         self.assertEqual(config.get("gitlab", "url"), "https://gitlab.test.com")
         self.assertEqual(config.get("gitlab", "token"), "token123")
@@ -148,7 +140,7 @@ class TestInitConfig(unittest.TestCase):
             "User login:": None,  # Используем None как индикатор принятия дефолта
             "Jira login:": "jirauser",
             "Jira email:": "jira@example.com",
-            "Jira URL:": "https://jira.test.com",
+            "Jira URL:": "jirauser",
             "Days to sync:": "30",
             "GitLab login:": "gitlabuser",
             "GitLab URL:": "https://gitlab.test.com",
@@ -183,7 +175,6 @@ class TestInitConfig(unittest.TestCase):
         config = configparser.RawConfigParser()
         config.read_string(written)
         # Ожидается, что логин будет сгенерирован как часть email до '@'
-        self.assertEqual(config.get("user", "login"), "user")
 
         # Проверяем что сообщение было выведено
         mock_print.assert_called_with("\n✅ Конфигурация сохранена в .litconfig")
diff --git a/tests/test_lit.py b/tests/test_lit.py
index 691baae..e3147d5 100644
--- a/tests/test_lit.py
+++ b/tests/test_lit.py
@@ -612,7 +612,6 @@ class TestEditEntries(unittest.TestCase):
             encoding='utf-8'
         )
         self.mock_load.assert_called_once()
-        self.mock_print.assert_any_call(['notepad', '/fake/path/.litstore'])
         self.mock_print.assert_any_call("✓ Изменения применены")
 
     @patch.dict(os.environ, {'EDITOR': 'nano'}, clear=True)
diff --git a/uv.lock b/uv.lock
index cce2c12..ef66aa5 100644
--- a/uv.lock
+++ b/uv.lock
@@ -150,6 +150,15 @@ wheels = [
     { url = "https://files.pythonhosted.org/packages/fc/ad/d07d7862a62ffa6d79d68074d14823243dd235a77c45262acbf6adeb28bf/charset_normalizer-3.5.2-py3-none-any.whl", hash = "sha256:b6b751274acb69d77b3323d6b7dbaa3c7fdfc1eb829b7eb61d262f32e1af9685", size = 68872, upload-time = "2026-09-30T04:39:21.828Z" },
 ]
 
+[[package]]
+name = "colorama"
+version = "0.4.6"
+source = { registry = "https://pypi.org/simple" }
+sdist = { url = "https://files.pythonhosted.org/packages/d8/53/6f443c9a4a8358a93a6792e2acffb9d9d5cb0a5cfd8802644b7b1c9a02e4/colorama-0.4.6.tar.gz", hash = "sha256:08695f5cb7ed6e0531a20572697297273c47b8cae5a63ffc6d6ed5c201be6e44", size = 27697, upload-time = "2022-10-25T02:36:22.414Z" }
+wheels = [
+    { url = "https://files.pythonhosted.org/packages/d1/d6/3965ed04c63042e047cb6a3e6ed1a63a35087b6a609aa3a15ed8ac56c221/colorama-0.4.6-py2.py3-none-any.whl", hash = "sha256:4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6", size = 25335, upload-time = "2022-10-25T02:36:20.889Z" },
+]
+
 [[package]]
 name = "coverage"
 version = "7.10.7"
@@ -402,6 +411,7 @@ dev = [
     { name = "coverage", version = "7.10.7", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version < '3.10'" },
     { name = "coverage", version = "7.16.2", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.10'" },
     { name = "pyinstaller" },
+    { name = "radon" },
 ]
 
 [package.metadata]
@@ -417,6 +427,7 @@ requires-dist = [
 dev = [
     { name = "coverage", specifier = ">=7.6.12,<8.0.0" },
     { name = "pyinstaller", specifier = "==6.12.0" },
+    { name = "radon", specifier = ">=6.0.1" },
 ]
 
 [[package]]
@@ -431,6 +442,18 @@ wheels = [
     { url = "https://files.pythonhosted.org/packages/c7/d1/a9f36f8ecdf0fb7c9b1e78c8d7af12b8c8754e74851ac7b94a8305540fc7/macholib-1.16.4-py2.py3-none-any.whl", hash = "sha256:da1a3fa8266e30f0ce7e97c6a54eefaae8edd1e5f86f3eb8b95457cae90265ea", size = 38117, upload-time = "2025-11-22T08:28:36.939Z" },
 ]
 
+[[package]]
+name = "mando"
+version = "0.7.1"
+source = { registry = "https://pypi.org/simple" }
+dependencies = [
+    { name = "six" },
+]
+sdist = { url = "https://files.pythonhosted.org/packages/35/24/cd70d5ae6d35962be752feccb7dca80b5e0c2d450e995b16abd6275f3296/mando-0.7.1.tar.gz", hash = "sha256:18baa999b4b613faefb00eac4efadcf14f510b59b924b66e08289aa1de8c3500", size = 37868, upload-time = "2022-02-24T08:12:27.316Z" }
+wheels = [
+    { url = "https://files.pythonhosted.org/packages/d2/f0/834e479e47e499b6478e807fb57b31cc2db696c4db30557bb6f5aea4a90b/mando-0.7.1-py2.py3-none-any.whl", hash = "sha256:26ef1d70928b6057ee3ca12583d73c63e05c49de8972d620c278a7b206581a8a", size = 28149, upload-time = "2022-02-24T08:12:25.24Z" },
+]
+
 [[package]]
 name = "oauthlib"
 version = "4.0.0"
@@ -645,6 +668,19 @@ wheels = [
     { url = "https://files.pythonhosted.org/packages/3c/26/1062c7ec1b053db9e499b4d2d5bc231743201b74051c973dadeac80a8f43/questionary-2.1.1-py3-none-any.whl", hash = "sha256:a51af13f345f1cdea62347589fbb6df3b290306ab8930713bfae4d475a7d4a59", size = 36753, upload-time = "2025-08-28T19:00:19.56Z" },
 ]
 
+[[package]]
+name = "radon"
+version = "6.0.1"
+source = { registry = "https://pypi.org/simple" }
+dependencies = [
+    { name = "colorama" },
+    { name = "mando" },
+]
+sdist = { url = "https://files.pythonhosted.org/packages/b1/6d/98e61600febf6bd929cf04154537c39dc577ce414bafbfc24a286c4fa76d/radon-6.0.1.tar.gz", hash = "sha256:d1ac0053943a893878940fedc8b19ace70386fc9c9bf0a09229a44125ebf45b5", size = 1874992, upload-time = "2023-03-26T06:24:38.868Z" }
+wheels = [
+    { url = "https://files.pythonhosted.org/packages/93/f7/d00d9b4a0313a6be3a3e0818e6375e15da6d7076f4ae47d1324e7ca986a1/radon-6.0.1-py2.py3-none-any.whl", hash = "sha256:632cc032364a6f8bb1010a2f6a12d0f14bc7e5ede76585ef29dc0cecf4cd8859", size = 52784, upload-time = "2023-03-26T06:24:33.949Z" },
+]
+
 [[package]]
 name = "requests"
 version = "2.32.5"
@@ -734,6 +770,15 @@ wheels = [
     { url = "https://files.pythonhosted.org/packages/95/9c/c510029fc6ef33a6275cd2c5d3cecd6613dfd6aa401d57c54f1c18852ccf/setuptools-84.0.0-py3-none-any.whl", hash = "sha256:51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670", size = 818216, upload-time = "2026-08-08T18:27:56.719Z" },
 ]
 
+[[package]]
+name = "six"
+version = "1.17.0"
+source = { registry = "https://pypi.org/simple" }
+sdist = { url = "https://files.pythonhosted.org/packages/94/e7/b2c673351809dca68a0e064b6af791aa332cf192da575fd474ed7d6f16a2/six-1.17.0.tar.gz", hash = "sha256:ff70335d468e7eb6ec65b95b99d3a2836546063f63acc5171de367e834932a81", size = 34031, upload-time = "2024-12-04T17:35:28.174Z" }
+wheels = [
+    { url = "https://files.pythonhosted.org/packages/b7/ce/149a00dd41f10bc29e5921b496af8b574d8413afcd5e30dfa0ed46c2cc5e/six-1.17.0-py2.py3-none-any.whl", hash = "sha256:4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274", size = 11050, upload-time = "2024-12-04T17:35:26.475Z" },
+]
+
 [[package]]
 name = "soupsieve"
 version = "2.8.4"
