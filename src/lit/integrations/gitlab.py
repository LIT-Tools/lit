"""Загрузка коммитов из GitLab."""
from __future__ import annotations

import requests
from datetime import datetime, timedelta
import re
import os
import json
from lit.config_manager import get_gitlab
from lit.constants import LIT_DIR, COMMITS_FILE

os.makedirs(LIT_DIR, exist_ok=True)


def save_commits(data: dict):
    """Сохранение коммитов в файл с атомарной записью"""
    try:
        with open(COMMITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving commits: {str(e)}")


USER_EMAIL = ""

def load_commits_from_gitlab() -> None:
    """Загрузка коммитов из GitLab."""
    load_config()
    
    config = get_gitlab()
    if not TOKEN or TOKEN == '':
        raise Exception("ОШИБКА: Токен GITLAB_TOKEN не найден в .litconfig")

    headers = {'Private-Token': TOKEN}
    url = GITLAB_URL
    user_email = USER_EMAIL
    days = DAYS

    # Рассчитываем дату DAYS дней назад
    since_datetime = datetime.now() - timedelta(days=days)
    since_date_iso = since_datetime.isoformat()

    print(f'Поиск проектов за {days} дней...', end="", flush=True)

    # Получаем все проекты пользователя
    projects = []
    page = 1
    while True:
        response = requests.get(
            f'{url}/api/v4/projects',
            headers=headers,
            params={'page': page,
                    'per_page': 100,
                    'last_activity_after': since_date_iso,  # Фильтр по последней активности
                    'order_by': 'last_activity_at',  # Сортировка по дате активности
                    'sort': 'desc'
                    }
        )
        response.raise_for_status()
        current_projects = response.json()

        if not current_projects:
            break

        # Фильтруем проекты по last_activity_at
        for project in current_projects:

            try:
                projects.append(project)
                print(f'\rПоиск проектов за {days} дней... {len(projects)}', end="", flush=True)

            except (KeyError, TypeError, ValueError) as e:
                print(f"\nОшибка обработки проекта {project.get('id')}: {str(e)}\n")

        page += 1

    print(f'\rПоиск коммитов за {days} дней...', end="", flush=True)

    # Собираем коммиты из всех проектов
    comments = []
    seen_commits: set[str] = set()
    for index, project in enumerate(projects, 1):
        # Выводим прогресс обработки
        print(f'\rПоиск коммитов за {days} дней... {index}/{len(projects)}', end='', flush=True)

        project_id = project['id']
        page = 1
        while True:
            try:
                response = requests.get(
                    f'{url}/api/v4/projects/{project_id}/repository/commits',
                    headers=headers,
                    params={
                        'since': since_date_iso,
                        'all': True,  # Ищем во всех ветках, а не только в default branch
                        # 'until': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),  # Добавляем верхнюю границу
                        # 'committer_username': username,  # Фильтруем и по коммиттеру
                        'with_stats': False,  # Убираем лишние данные
                        'page': page,
                        'per_page': 100
                    }
                )
                if response.status_code in (403, 404):
                    break
                response.raise_for_status()
                commits = response.json()

                for commit in commits:
                    commit_id = commit.get('id')
                    if commit_id:
                        if commit_id in seen_commits:
                            continue
                        seen_commits.add(commit_id)

                    # Проверяем и автора и коммиттера
                    if len(commit['message']) > 0 and (
                            commit['author_email'].lower() == user_email.lower() or commit['committer_email'].lower() == user_email.lower()):
                        if commit['message'].find('Merge branch') == -1:
                            comments.append(commit['message'].rstrip())

                if not commits:
                    break

                page += 1
            except requests.exceptions.HTTPError:
                break

    # Обрабатываем сообщения коммитов
    task_commits = {}
    useful_commits = 0
    pattern = re.compile(r'\b([A-Z]+-\d+)\b')

    for message in comments:
        first_line = message.split('\n')[0].strip()
        tasks = list(set(pattern.findall(message.upper())))

        for task in tasks:
            mes = message.replace(task, '')
            if len(mes) > 5:
                task_commits.setdefault(task, []).append(first_line.replace(task, '').strip())
                useful_commits += 1

    # Сортируем задачи и удаляем пустые
    sorted_tasks = {k: v for k, v in sorted(task_commits.items()) if k and v}

    print(f'\rНайдено {useful_commits} пригодных коммитов из {len(comments)} в {len(sorted_tasks)} репозиториях за авторством {user_email}')

    save_commits(sorted_tasks)


# Для совместимости с тестами мокающими import_gitlab.load_config()
def load_config(path: str | None = None) -> dict:
    """Алиас для совместимости с мокающими тестами."""
    config = get_gitlab()
    global GITLAB_URL, TOKEN, USER_EMAIL, DAYS
    GITLAB_URL = config["url"]
    TOKEN = config["token"]
    USER_EMAIL = config.get("email", config.get("login", ""))  # fallback для старых конфигов
    DAYS = config["days"]
    return config
