# Восстановление потерянных изменений `dev` после рефакторинга

> Контекст: ветка `dev` содержала 12 коммитов (апрель 2026), которые не
> попали в ветку `feature/src-layout` после переезда poetry→uv и
> рефакторинга. Перенести мерджем нельзя — код переехал (`lit.py` →
> `src/lit/__init__.py`, `import_gitlab.py` → `src/lit/integrations/gitlab.py`,
> `test_*.py` → `tests/`, poetry → uv, плоская структура → `src/lit/`).
> Каждое изменение переносится вручную в новую структуру.
>
> **Флоу:** взять коммит(ы) → прочитать `git show <hash>` → найти аналог
> в текущем дереве → внести правку → прогнать тесты/smoke → галочка →
> коммит. Если изменение уже неактуально — отметить `[-]` с причиной.

## Соглашения

- ✅ сделано; 🔄 в работе; ⏭ пропущено (неактуально); ☐ в очереди.
- «Аналог»: для `import_gitlab.py` → `src/lit/integrations/gitlab.py`,
  `test_import_gitlab.py` → `tests/test_gitlab.py`, `test_lit.py` →
  `tests/test_lit.py`, `lit.py` → `src/lit/__init__.py` (или `core/`,
  `integrations/` — по контексту), `init.py` → `src/lit/init.py`.
- После каждого шага: `uv run coverage run -m unittest discover && uv
  run coverage report -m` → `≥44 OK`, `TOTAL ≥82%`; smoke
  (`lit --help / -v / status` → `exit=0`).
- Коммит после каждого шага; Conventional Commits (см.
  `.agents/skills/git-commit-convention/SKILL.md`).
- `git show --stat HEAD` перед коммитом — ровно ожидаемые файлы.

---

## 📋 Чек-лист

### 🟢 Шаг A — Misc (независимые мелкие правки)

- [ ] `7f8e5e83` — `refactor: removed print` (лишний `print(cmd)` в
  `edit_entries`)
- [ ] `2bb20664` — `docs: fixed duplicate path in PATH during installation`
  (Windows install в README)
- [ ] `4a19517b` — `docs: added bug to check list` (в README-планы
  добавить баг «после `pull` нужен перезапуск REPL»)

### 🟢 Шаг B — Dev-tools: CRAP-анализ

- [ ] `1613c1d1` — `test: added calc CRAP` (новый `calc_crap.py` +
  `.gitignore` `cc.json`/`coverage.json` + `radon` в dev + README test
  section с `coverage run --branch`, `coverage json`, `radon cc`)

### 🟢 Шаг C — Документация: пример `.litconfig`

- [ ] `e8760eb0` — `docs: fixed example .litconfig`
  (уточнить, не пересекается ли с `1e5cea6b` из Шага D; если
  дубликат — отметить `[-]`)

### 🔴 Шаг D — Config schema cleanup (связанный батч, делать вместе)

Все 6 коммитов трогают `.litconfig`-схему и её потребителей. По
отдельности тесты будут красными. Один шаг = один коммит.

- [ ] `abfafc49` — `refactor: removed field of config user login`
- [ ] `c98db846` — `refactor: removed field of config jira email`
- [ ] `ed5290ce` — `refactor: removed field of config gitlab login`
- [ ] `63eb82c4` — `feat(config): dynamic URLs by user domain` (zebrains)
- [ ] `2ed64bb9` — `refactor(config): added hint for token Select scopes: api`
- [ ] `1e5cea6b` — `docs: fixed example .litconfig`

### 🟡 Шаг E — `UPDATE.md` (draft фичи)

- [ ] `8af3c39f` — `docs: added UPDATE.md` (черновик auto-update; перенести
  как draft, не в код)

### ⚪ Не переносить

- `CHANGELOG.md`, `poetry.lock`, bump `1.0.1 → 1.1.0` — это артефакты
  старой ветки. `CHANGELOG` перегенерирует `release-please`, `uv.lock`
  заменил `poetry.lock`, версия в `pyproject.toml` уже `1.1.0`.

---

## 🎯 Рекомендации по шагам

### Шаг A — Misc

**Коммиты:** `7f8e5e83`, `2bb20664`, `4a19517b`.

**Аналог в текущем дереве:**
- `print(cmd)` — в `src/lit/core/worklog_manager.py`, метод
  `edit_entries` (после переноса `WorklogManager` в `core/`).
  Проверьте: `grep -rn "print(cmd)" src/lit/`.
- Windows install script — `README.md`, блок «🪟 Windows».
- README-планы — `README.md`, блок «🔮 Планы развития».

**Что делать:**
1. `git show 7f8e5e83` — посмотреть diff. Удалить `print(cmd)` в
   `edit_entries`, добавить/поправить `assert` в
   `tests/test_lit.py` (если он есть на этот print — сейчас, вероятно,
   нет, потому что `print` уже убран? проверить
   `grep -n "print(cmd)\|assert_any_call(\['notepad'" tests/`).
2. `git show 2bb20664` — посмотреть diff, применить к README, блок
   Windows.
3. `git show 4a19517b` — посмотреть, какой пункт добавлен в
   «Планы развития» (`pull` требует перезапуска REPL). Добавить в
   README, если ещё нет.

**DoD:**
- Тесты ≥44 OK, покрытие ≥82%.
- Smoke `exit=0`.
- `git show --stat HEAD` — только `README.md` (+ `tests/test_lit.py`
  и `src/lit/core/worklog_manager.py`, если `print` был).

**Коммит:** `chore: restore misc changes from dev (print, README)`
или три отдельных коммита `refactor: remove debug print in
edit_entries`, `docs: dedup PATH in Windows install`, `docs: note
pull-in-REPL bug in plans` — если хочется атомарности 1:1.

---

### Шаг B — Dev-tools CRAP

**Коммит:** `1613c1d1`.

**Аналог:** `calc_crap.py` в корень, `.gitignore`, `pyproject.toml` (но
у нас `[dependency-groups] dev = [...]`, а не `[tool.poetry.group.dev]`),
README test-секция.

**Что делать:**
1. `git show 1613c1d1` — посмотреть diff.
2. Создать `calc_crap.py` (скопировать из `git show`, кодировка UTF-8,
   без изменений).
3. `.gitignore`: добавить `cc.json`, `coverage.json` после
   `.coverage`.
4. `uv add --dev radon` — обновит `pyproject.toml` и `uv.lock`
   правильно (не копировать poetry-секцию руками).
5. README «🛠 Тестирование»: заменить блок тестов на
   `coverage run --branch -m unittest discover`, `coverage report -m`,
   `coverage json -o coverage.json`, `radon cc . -j -O cc.json`,
   `python calc_crap.py`.
6. Проверить: `uv run python calc_crap.py` → сообщает «cc.json не
   найден» (если не запускали) — это норм. Если запустить всё по
   README — должен напечатать метрики.

**DoD:**
- Тесты ≥44 OK, покрытие ≥82%.
- `uv run python calc_crap.py; echo "exit=$?"` — после прогона
  coverage/radon печатает CRAP-таблицу, `exit=0`.
- `git show --stat HEAD` — `calc_crap.py`, `.gitignore`,
  `pyproject.toml`, `uv.lock`, `README.md`.

**Коммит:** `chore: add CRAP metric analysis tooling`

**Опционально:** можно разбить на два (`test: add calc_crap.py` +
`chore: add radon dev-dep`), но атомарность по `1613c1d1` проще.

---

### Шаг C — Пример `.litconfig`

**Коммит:** `e8760eb0`.

**Что делать:**
1. `git show e8760eb0` — что именно поправлено в README-примере.
2. **Проверить**, не дублирует ли `1e5cea6b` (Шаг D). Если да —
   отметить `[-]` и закрыть.
3. Если правка независима (например, комментарий к `editor`) —
   применить к README, блок «⚙️ Конфигурация».

**DoD:**
- README-пример `.litconfig` соответствует **текущей** (после шага D)
  схеме, а не старой. Если шаг D ещё не сделан — этот шаг делать
  **после** D.
- Тесты ≥44 OK.

**Коммит:** `docs: update .litconfig example`

**⚠️ Порядок:** если `e8760eb0` меняет пример под старую схему (с
`login`/`email`), его надо делать **после** шага D, иначе пример будет
противоречить коду. По `git show` — если там ничего не про удалённые
поля, можно и до.

---

### Шаг D — Config schema cleanup (🔴 самый рискованный)

**Коммиты (батч):** `abfafc49`, `c98db846`, `ed5290ce`, `63eb82c4`,
`2ed64bb9`, `1e5cea6b`.

**Почему батч:** `abfafc49` убирает `login` из `init.py` и
`test_init.py`; если не убрать `login` из `config_manager.get_user()`
(`c98db846`-сосед), `add_entry` может упасть. Все шесть — одно изменение
схемы.

**Что делать:**

1. **Обследование (обязательно):**
   ```bash
   grep -rn "login\|email" src/lit/config_manager.py src/lit/init.py
   grep -rn "get_user\|get_jira\|get_gitlab" src/lit/ --include="*.py"
   grep -rn "login\|email" tests/ --include="*.py"
   grep -rn "TARGET_USER\|USER_EMAIL\|author_email" src/lit/integrations/gitlab.py
   ```

2. **`src/lit/config_manager.py`:**
   - `get_user()` → вернуть `{email, editor}` (без `login`).
   - `get_jira()` → вернуть `{login, pass, url, days}` (без `email`;
     `login` остаётся — это Jira-логин).
   - `get_gitlab()` → вернуть `{email, url, token, days}` (без `login`).
   - **Совместимость:** для пользователей со старым конфигом
     (`[gitlab] login` есть, `email` нет) — в `get_gitlab()`
     `email = email or login`. Одна строка, спасает от «обновите
     конфиг».

3. **`src/lit/init.py`:**
   - Не спрашивать `user.login`, `jira.email`, `gitlab.login`.
   - Добавить zebrains-логику: `is_zebrains_user = 'zebrains' in
     domain`; fallback URL для jira/gitlab подставляется только для
     zebrains-доменов.
   - В подсказке токена: `Select scopes: api`.

4. **`src/lit/integrations/gitlab.py`** (это то, что в diff
   `import_gitlab.py`):
   - `TARGET_USER = config.get('gitlab', 'login')` → `USER_EMAIL =
     config.get('gitlab', 'email')`.
   - Удалить `requests.get(f'{GITLAB_URL}/api/v4/user', ...)` — этот
     запрос раньше был нужен, но всё равно перезаписывался на
     `TARGET_USER`. Теперь мёртвый.
   - Фильтр: `commit['author_email'].split("@")[0].lower() ==
     username.lower()` → `commit['author_email'].lower() ==
     USER_EMAIL.lower()`. Аналогично для committer.
   - Print в конце: `за авторством {USER_EMAIL}`.

5. **`tests/test_init.py`:** убрать `login`/`email`-поля из
   `text_answers` и `assert` (посмотреть `git show abfafc49` и
   `c98db846` и `ed5290ce` — там точные диффы тестов).
   Обновить `existing_config` в `test_init_with_existing`.

6. **`tests/test_gitlab.py`** (бывш. `test_import_gitlab.py`):
   - `import_gitlab.TARGET_USER = 'test_user'` → `USER_EMAIL =
     'test_user@example.com'`.
   - Убрать мок `/api/v4/user` из `side_effect`-списков (три теста:
     `test_load_commits_from_gitlab`, `test_commit_filtering`,
     `test_message_parsing`).
   - Убрать `assert_any_call` для `https://gitlab.example.com/api/v4/user`.
   - Тестовые данные коммитов: `author_email` уже полный email? —
     проверить; `git show ed5290ce` покажет.

7. **README** (это `1e5cea6b` + часть `e8760eb0`): пример
   `.litconfig` — `[user] email + editor`, `[jira] login + pass + url +
   days` (без `email`), `[gitlab] email + url + token + days` (без
   `login`). Комментарий `editor` с примером Notepad++.

**DoD:**
- Тесты ≥44 OK, покрытие ≥82% (**после батча**, не внутри).
- Smoke `exit=0`.
- `uv run python -c "from lit.config_manager import get_user,
  get_jira, get_gitlab; print(get_user()); print(get_jira());
  print(get_gitlab())"` → все три без ошибок.
- Старый конфиг с `[gitlab] login` (без `email`) — `get_gitlab()`
  возвращает `email` из `login` (тест на это добавить в
  `tests/test_init.py` или `tests/test_config_manager.py`, если есть).
- `grep -rn "TARGET_USER\|/api/v4/user" src/lit/ tests/` — пусто.
- `git show --stat HEAD` — `src/lit/config_manager.py`,
  `src/lit/init.py`, `src/lit/integrations/gitlab.py`,
  `tests/test_init.py`, `tests/test_gitlab.py`, `README.md`.

**Коммит (один на весь батч):**
```
refactor(config): simplify .litconfig schema

Remove deprecated fields (user.login, jira.email, gitlab.login) and
switch GitLab commit filtering to email (was login-based, silently
failed when login != email). Add zebrains-domain defaults for URLs.

Restored from dev commits: abfafc49, c98db846, ed5290ce, 63eb82c4,
2ed64bb9, 1e5cea6b.
```

**Если стало страшно:** можно разбить на 2 коммита — (1) config_manager
+ init + tests (убрать поля), (2) gitlab.py (email-фильтр). Но обе
части должны быть в одном шаге, чтобы прогон тестов был зелёным.

---

### Шаг E — `UPDATE.md` draft

**Коммит:** `8af3c39f`.

**Что делать:**
1. `git show 8af3c39f` — посмотреть содержимое.
2. Создать `docs/UPDATE.md` (или `docs/drafts/auto-update.md`), не
   `UPDATE.md` в корне — корень уже забит.
3. В шапку добавить:
   ```markdown
   > **DRAFT.** Не реализовано. Черновик фичи auto-update из dev-ветки
   > (апрель 2026). В код не переносить до отдельного цикла.
   ```

**DoD:**
- Тесты ≥44 OK (файл в docs, на тесты не влияет).
- `git show --stat HEAD` — `docs/UPDATE.md` (новый).

**Коммит:** `docs: add auto-update draft from dev`

---

## 🔮 После восстановления

Когда все шаги закрыты:
1. Обновить `REFACTORING.md` — убрать упоминания «восстановить
   потерянные коммиты», если были.
2. Проверить `README.md` «Планы развития» — выровнять с тем, что
   добавлено в шаге A и что уже сделано.
3. Переходить к **циклу Jira v3** (`REFACTORING_LOOP.md`).

## 📚 Уроки

Эти уроки — повод проверить `docs/refactoring-log.md` и добавить
секцию «2026-04: восстановление dev»:
- «Откат на старый коммит перед рефакторингом = потеря работы
  параллельной ветки. Создавать `feature/*` **от актуального** `dev`/
  `master`, а не от старого тега».
- «Если `dev` ушёл вперёд, а ты рефакторишь с другого места — `git
  log dev ^HEAD` покажет, что потеряешь, до начала работы».
- «Не мерджить, если код переехал: `git show <hash>` + вручную».

---

## 🤖 Готовые промты для агента

### Промт на Шаг A

````markdown
# Задача: Восстановить из dev мелкие правки (print, README)

Ветка `feature/src-layout`, HEAD — коммит с восстановлением планов.
Нужно перенести из ветки `dev` три коммита в текущую структуру:

1. `7f8e5e83` — `refactor: removed print` — удалить `print(cmd)` в
   `edit_entries` (сейчас в `src/lit/core/worklog_manager.py`).
2. `2bb20664` — `docs: fixed duplicate path in PATH` — Windows install
   в `README.md`, блок «🪟 Windows».
3. `4a19517b` — `docs: added bug to check list` — добавить в README,
   «🔮 Планы развития»: баг «после `pull` нужно перезапускать REPL».

## Обследование

```bash
git show 7f8e5e83
git show 2bb20664
git show 4a19517b
grep -rn "print(cmd)" src/lit/
grep -n "installPath\|USERPROFILE" README.md
grep -n "pull\|перезапуск" README.md
```

## Что сделать

- Каждое изменение применить к **текущей** структуре (`src/lit/`,
  не плоские модули).
- Если по `git show` видно, что правка уже неактуальна (например,
  код уже другой) — **отметить в отчёте** и пропустить, не выдумывать.

## DoD

- `uv run coverage run -m unittest discover && uv run coverage report -m`
  → ≥44 OK, ≥82%.
- `uv run lit --help / -v / status` → `exit=0`.
- `git show --stat HEAD` — ровно: `README.md` (+ `tests/test_lit.py`,
  `src/lit/core/worklog_manager.py`, если `print` был).
- Если в `tests/test_lit.py` был assert на `print(cmd)` — убрать его
  в том же коммите.

## Коммит

Можно одним:
```
chore: restore misc changes from dev (print, README)
```
или тремя (атомарно):
- `refactor: remove debug print in edit_entries`
- `docs: dedup PATH in Windows install`
- `docs: note pull-in-REPL bug in plans`

## Ограничения

- Только `README.md` (+ 2 файла в первом коммите).
- Не трогать `pyproject.toml`, `config_manager.py`, `init.py`,
  `integrations/*`, тесты кроме `assert` на `print`.
- Не запускать `uv run lit` без аргументов, `init`, `push`, `add`,
  `edit`.
- `echo exit=$?` на каждой проверке. Traceback = провал.

## Отчёт

1. Статус, попытки.
2. Diff по каждому файлу (кратко).
3. `git log --oneline -1`.
4. Если что-то уже неактуально — какое и почему.
5. Не начинать Шаг B.