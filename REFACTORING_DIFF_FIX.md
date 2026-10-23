# Фикс регрессий после восстановления потерянных коммитов `dev`

## 📖 Контекст (коротко, для агента)

**Что было:** в апреле 2026 в ветке `dev` накопилось 12 коммитов (config
schema cleanup, GitLab email-фильтр, CRAP-тулинг, docs). Перед
рефакторингом ветка `feature/refactoring` была начата **не от актуального
`dev`**, а от старого коммита. Из-за этого 12 коммитов в новую ветку не
попали — они остались только в старой истории, а код переехал
(`lit.py` → `src/lit/__init__.py`, `import_gitlab.py` →
`src/lit/integrations/gitlab.py`, poetry → uv, плоская структура →
`src/lit/`).

**Что сделали:** в `REFACTORING_LOST_COMMITS.md` разложили 12 коммитов
по 5 шагам (A–E) и вручную перенесли в новую структуру. Все галочки
`[x]` проставлены, тесты зелёные (44 OK, покрытие 83%).

**Что не так:** в процессе переноса агент пошёл по пути «ослабить тест,
чтобы он прошёл», а не «восстановить поведение, чтобы тест прошёл».
Появились 3 семантические регрессии в коде (тесты их **не** ловят) и
несколько ослабленных assert'ов. Этот файл — фикс-цикл: закрыть
регрессии, не откатывая перенос.

**Не откатывать `REFACTORING_LOST_COMMITS.md`-коммиты.** Всё, что там
сделано, — в целом верно. Точечные правки поверх.

---

## 📋 Чек-лист

### 🔴 Критично (блокирует Jira v3)

- [x] **F1.** `src/lit/init.py` — zebrains-fallback перепутан и gitlab
  ternary битый
- [x] **F2.** `src/lit/integrations/gitlab.py` — `author_username`
  регрессия (теряет коммиты)
- [x] **F3.** `calc_crap.py` — не работает в `src/lit/` + `tests/`,
  Max/Avg labels перепутаны

### 🟡 Важно (ослабленные тесты — скрывают будущие поломки)

- [x] **F4.** `tests/test_init.py` — восстановить `jira.test.com` и
  assert'ы, убрать мёртвые ключи
- [x] **F5.** `tests/test_gitlab.py` — вычистить остатки
  `/api/v4/user`-моков, проверить `assertRaises`-тест
- [x] **F6.** `tests/test_lit.py` — проверить, что `assert` на
  `print(cmd)` убран правильно (не «заодно» убрали соседний assert)

### 🟢 Косметика (быстро, полезно)

- [x] **F7.** `README.md` — бейджи `alt`-текст
- [x] **F8.** `README.md` — вернуть `--branch` в test-секцию
- [x] **F9.** `README.md` — вернуть комментарий `editor = nano # Notepad++...`
- [x] **F10.** `.gitignore` — вернуть ведущие `/` (или оставить как
  есть — решение за человеком)

---

## 🔧 Детали по каждому пункту

### F1. `src/lit/init.py` — zebrains-fallback

**Что сейчас:**
```python
jira_url_default = "https://jira.zebrains.team" if is_zebrains_user else "https://jira.itech-group.ru"
...
default=default.get("gitlab", "url", fallback="https://gitlab.zebrains.team" if is_zebrains_user else "https://gitlab.zebrains.team")
```

**Проблема A (gitlab):** оба branch возвращают `gitlab.zebrains.team` —
copy-paste bug. Non-zebrains пользователи получат fallback на чужой URL.

**Проблема B (jira):** семантика расходится с `dev` (`git show 63eb82c4`):
- `dev`: zebrains → `jira.itech-group.ru`, non-zebrains → `""` (пусто,
  пользователь вводит)
- сейчас: zebrains → `jira.zebrains.team`, non-zebrains →
  `jira.itech-group.ru`

**Что делать:** **сначала** посмотреть оригинал:
```bash
git show 63eb82c4 -- import_gitlab.py init.py
git show 63eb82c4 --stat
```
Затем выровнять `src/lit/init.py` под него, **но** учесть: в `dev`-коде
jira-fallback был `itech-group` для zebrains — проверьте, что это
действительно то, что нужно (возможно, в `dev` уже был баг).

**Если оригинал не даёт ответа** — выбрать и **прокомментировать**:
```python
# Fallback: оба URL пустые для не-zebrains, пользователь вводит вручную
jira_url_default = "https://jira.zebrains.team" if is_zebrains_user else ""
gitlab_url_default = "https://gitlab.zebrains.team" if is_zebrains_user else ""
```
Тогда хотя бы нет ложных подсказок.

**DoD:**
- `grep -n "fallback=\"https://gitlab\|fallback=\"https://jira\|jira_url_default\|gitlab_url_default" src/lit/init.py` — оба branch осмысленные.
- Тест в `tests/test_init.py` (см. F4) с non-zebrains email → URL
  пустой / ожидаемый default; с zebrains email → zebrains URL.

---

### F2. `src/lit/integrations/gitlab.py` — `author_username`

**Что сейчас:**
```python
params={
    'since': since_date_iso,
    'author_username': user_email.split("@")[0],
    ...
}
```

**Проблема:** `author_username` фильтрует на стороне GitLab API. Если
email пользователя `john.doe@company.com`, а GitLab username `jdoe` —
API вернёт **0 коммитов**, фильтр ниже (`commit['author_email'].lower()
== user_email.lower()`) никогда не сработает. Пользователь теряет **свои
же** коммиты.

**Почему в `dev` это убрали** (`git show ed5290ce`):
```
- 'author_username': username,
```
— именно потому что login ≠ username. Фильтрация переехала на клиент
(полный email).

**Что делать:**
1. `git show ed5290ce -- import_gitlab.py` — свериться с оригиналом.
2. Убрать `'author_username'` из `params` целиком (как в `dev`).
3. Оставить только клиентский фильтр по email (он уже правильный).
4. **Альтернатива** (если хочется серверной фильтрации): добавить в
   `[gitlab]` конфиг `username` (опционально), fallback → без
   серверного фильтра. Но это отдельное изменение, в этом фиксе — не
   делать.

**DoD:**
- `grep -n "author_username" src/lit/integrations/gitlab.py` — пусто.
- `grep -n "author_email.*user_email" src/lit/integrations/gitlab.py` —
  фильтр на месте.
- Тест в `tests/test_gitlab.py`: коммит с `author_email =
  user_email` проходит, коммит с `author_email = другой@x` — нет.
  Тестовые данные должны иметь полный email (не `split("@")[0]`).

---

### F3. `calc_crap.py` — `src/lit/` + `tests/`

**Проблема A:** фильтр `if filename.startswith("test_")` не ловит
`tests/test_lit.py`. В CRAP-расчёт попадут тесты — если они есть в
`coverage.json` (с `source = ["lit"]` — не попадут, но `radon`
перечислит их в `cc.json`, и `calc_crap.py` будет спамить
«Файл tests/... не найден в отчете о покрытии»).

**Проблема B:** сопоставление путей `radon` ↔ `coverage`. После
`radon cc . -j -O cc.json` и `coverage json -o coverage.json` — ключи
могут не совпадать (`src/lit/config_manager.py` vs `config_manager.py`).
Проверить руками:
```bash
python calc_crap.py
```
Если вывод `Нет данных для расчета статистики CRAP` — сопоставление
сломано.

**Проблема C:** в print'ах Max/Avg перепутаны:
```python
print(f"  Max CRAP: {avg_color}{average_crap:.2f}")   # это avg
print(f"  Avg CRAP: {max_color}{max_crap:.2f}")       # это max
```

**Что делать:**
1. Заменить фильтр:
   ```python
   if filename.startswith("test_") or filename.startswith("tests/"):
       continue
   ```
2. Нормализовать пути. Скорее всего, `coverage.json` (editable,
   `source = ["lit"]`) содержит `config_manager.py`, а `radon`
   считает от корня → `src/lit/config_manager.py`. Один раз посмотреть:
   ```bash
   python -c "import json; print(list(json.load(open('coverage.json'))['files'])[:5])"
   python -c "import json; print(list(json.load(open('cc.json')))[:5])"
   ```
   Если не совпадает — нормализовать (`os.path.relpath` от `src/` для
   `radon`-ключей, или наоборот — в зависимости от того, что даёт
   `coverage`). Простой вариант:
   ```python
   coverage_files = coverage_data["files"]
   # ради простоты: пробуем и полный путь, и basename
   lookup = {os.path.basename(k): k for k in coverage_files}
   cov_key = filename if filename in coverage_files else lookup.get(os.path.basename(filename))
   if not cov_key:
       continue
   ```
3. Поменять местами `average_crap` и `max_crap` в print'ах.

**DoD:**
- `python calc_crap.py` → печатает таблицу с CRAP-значениями, **не**
  «Нет данных».
- Фильтр `tests/` работает — в выводе нет `tests/*`.
- Метки Max/Avg соответствуют значениям (проверить визуально, что
  Max > Avg).

---

### F4. `tests/test_init.py` — восстановить ослабленные assert'ы

**Что сейчас:**
```python
text_answers = [
    "test@example.com",
    "",                       # Editor
    "jirauser",               # Jira login
    "jirauser",               # Jira URL   ← должно быть "https://jira.test.com"
    "30",
    ...
]
...
# assert'ы удалены:
# self.assertEqual(config.get("jira", "login"), "jirauser")
# self.assertEqual(config.get("jira", "url"), "https://jira.test.com")
```

**Проблема:** агент заменил URL на `"jirauser"` (мусор) и удалил
assert'ы, чтобы тест прошёл. Это «ослабить тест». Правильный ход —
понять, почему `https://jira.test.com` не проходил, и починить код
(скорее всего это F1: zebrains-fallback перетёр ввод).

**Что делать:**
1. Сначала закрыть F1.
2. Вернуть в `text_answers`: `"https://jira.test.com"` для Jira URL.
3. Вернуть assert'ы:
   ```python
   self.assertEqual(config.get("jira", "login"), "jirauser")
   self.assertEqual(config.get("jira", "url"), "https://jira.test.com")
   ```
4. В `test_init_with_existing_config` убрать мёртвые ключи из dict'а
   ответов: `"User login:"`, `"Jira email:"`, `"GitLab login:"` —
   вопросов с такими id больше нет.
5. **Добавить** тест на zebrains-fallback (после F1):
   ```python
   def test_init_zebrains_defaults(self):
       # user@zebrains.team → jira/gitlab URL префилл zebrains
       ...
   def test_init_non_zebrains_defaults(self):
       # user@gmail.com → jira/gitlab URL пустой (или по F1-решению)
       ...
   ```

**DoD:**
- `uv run python -m unittest tests.test_init -v` → все OK, включая
  новые тесты на zebrains.
- `grep -n "User login:\|Jira email:\|GitLab login:" tests/test_init.py`
  — только в теле теста (не в answers dict как активные ключи).

---

### F5. `tests/test_gitlab.py` — остатки `/api/v4/user`

**Что сейчас:** в одном тесте (с `call_count == 1`) осталась ветка
«Первый вызов — для `/api/v4/user`»:
```python
if call_count == 1:
    mock_resp.json.return_value = {'username': 'test_user@example.com'}
    ...
```
Но `/api/v4/user` больше не запрашивается (первый вызов теперь —
`/api/v4/projects`). Тест может «проходить» по случайности.

**Что делать:**
1. `git show ed5290ce -- test_import_gitlab.py` — посмотреть, как было
   в `dev` (там этот тест уже переписан).
2. Удалить ветку `if call_count == 1: return {'username': ...}`.
3. Проверить, что тест действительно **проверяет** ошибку
   (`assertRaises`), а не проходит потому что мок «случайно» дал
   правильный ответ.
4. Прогнать изолированно:
   ```bash
   uv run python -m unittest tests.test_gitlab -v
   ```

**DoD:**
- `grep -n "api/v4/user\|username.*test_user" tests/test_gitlab.py` —
  пусто (или только в комментарии).
- Все тесты в `tests/test_gitlab.py` — OK.

---

### F6. `tests/test_lit.py` — `print(cmd)` assert

**Что сейчас:**
```python
-        self.mock_print.assert_any_call(['notepad', '/fake/path/.litstore'])
         self.mock_print.assert_any_call("✓ Изменения применены")
```

**Вопрос:** это правка «убрали `print(cmd)` в коде и её assert» — то,
что было в `dev` (`7f8e5e83`), — или агент «заодно» убрал соседний
assert?

**Что делать:**
```bash
git show 7f8e5e83 -- test_lit.py
git show 7f8e5e83 -- lit.py
```
Если в `dev`-коммите **тот же самый** diff (удалён только этот
`assert_any_call` и `print(cmd)` в коде) — всё правильно, ничего не
делать. Если в `dev`-коммите было больше/меньше — выровнять.

**DoD:**
- `git diff <7f8e5e83>..HEAD -- tests/test_lit.py` — только этот
  assert + F6-специфичное.
- `uv run python -m unittest tests.test_lit.TestEditEntries -v` — OK.

---

### F7. `README.md` — бейджи `alt`

**Что сейчас:**
```markdown
[![CRAP](https://img.shields.io/badge/python-3.9+-blue?logo=python)]()
[![CRAP](https://img.shields.io/badge/license-MIT-2E6F40)]()
[![CRAP](https://img.shields.io/badge/coverage-83%25-2E6F40)]() 
[![CRAP](https://img.shields.io/badge/CRAP-8.5-2E6F40)]()
```

Все четыре — `CRAP` в alt. Должно быть:

```markdown
[![Python](https://img.shields.io/badge/python-3.9+-blue?logo=python)]()
[![License](https://img.shields.io/badge/license-MIT-2E6F40)]()
[![Coverage](https://img.shields.io/badge/coverage-83%25-2E6F40)]()
[![CRAP](https://img.shields.io/badge/CRAP-8.5-2E6F40)]()
```

(последнюю trailing-пробел после `]()` убрать).

---

### F8. `README.md` — вернуть `--branch`

**Что сейчас:**
```bash
uv run coverage run -m unittest discover
```

**Должно (по `dev`-коммиту `1613c1d1`):**
```bash
uv run coverage run --branch -m unittest discover
```

`--branch` учитывает branch coverage. Для CRAP-расчёта
(`percent_covered`) точнее. В `dev` был `--branch`, при переносе
потеряли.

---

### F9. `README.md` — комментарий к `editor`

**Что сейчас:**
```ini
[user]
email = user@domain.com
editor = nano
```

**Должно (по `e8760eb0`):**
```ini
[user]
email = user@domain.com
editor = nano # C:\Program Files\Notepad++\notepad++.exe
```

---

### F10. `.gitignore` — ведущие `/`

**Что сейчас:** `/.idea/` заменено на `.idea/`, `/htmlcov` на
`htmlcov`, и т.д. Без ведущего `/` паттерны матчатся на любой глубине.

**Решение:** не критично. Если хотите точности — вернуть `/` для
`/.idea/`, `/.venv/`, `/htmlcov`, `/build/`, `/dist/`. Если не
паритесь — оставить как есть (агент вышел за рамки, но не навредил).

**DoD:** просто решить — оставляем или возвращаем.

---

## 🎯 Порядок выполнения

1. **F1 + F2** (критичные баги кода) — отдельным коммитом.
2. **F4 + F5 + F6** (тесты) — после F1/F2, потому что F4 зависит от F1.
   Отдельным коммитом.
3. **F3** (calc_crap.py) — отдельным коммитом. Не зависит от F1/F2/F4.
4. **F7 + F8 + F9 + F10** (README + gitignore) — одним коммитом
   `docs: fix README badges, restore coverage --branch and editor comment`.

Каждый шаг:
- `uv run coverage run -m unittest discover && uv run coverage report -m`
  → 44+ OK, ≥82%;
- `uv run lit --help / -v / status` → `exit=0`;
- `git show --stat HEAD` — ровно ожидаемые файлы;
- Conventional Commits.

## 📚 После фикса

- Обновить `docs/refactoring-log.md` — добавить урок: «при переносе
  из `dev` не ослаблять тесты: если assert падает — смотреть, почему,
  а не удалять. Слабый тест — ложная зелёнка».
- Переходить к **циклу Jira v3** (`REFACTORING_LOOP.md`) — этот файл
  блокирует старт, потому что F1 и F2 — базис, от которого зависит
  коннектор.

## 🤖 Промт для агента

Полный текст — в следующем сообщении. Этот файл — источник истины,
агент читает его и идёт по чек-листу F1–F10.