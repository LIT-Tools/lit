import requests
from datetime import datetime, timedelta
import re
import os
import json
import configparser

#TODO В утилсы
def save_commits(data: dict):
    """Сохранение коммитов в файл с атомарной записью"""
    try:
        with open(COMMITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving commits: {str(e)}")


#TODO Конфигурация дублируется, вынести в отдельный код
LIT_DIR = os.path.join(os.path.expanduser("~"), ".lit")
os.makedirs(LIT_DIR, exist_ok=True)
COMMITS_FILE = os.path.join(LIT_DIR, "commits.json")
CONFIG_FILE = os.path.join(LIT_DIR, ".litconfig")

GITLAB_URL = ''
# USER_EMAIL = config.get('jira', 'email')
TOKEN = ''
TARGET_USER = ''
DAYS = ''

def load_config():
    global GITLAB_URL, TOKEN, TARGET_USER, DAYS
    # Создаем конфиг-парсер с сохранением регистра
    config = configparser.RawConfigParser()
    config.optionxform = lambda option: option  # Отключаем авто-преобразование в lowercase
    config.read(CONFIG_FILE)

    GITLAB_URL = config.get('gitlab', 'url')
    TOKEN = config.get('gitlab', 'token')
    TARGET_USER = config.get('gitlab', 'login')
    DAYS = int(config.get('gitlab', 'days'))

def load_commits_from_gitlab():
    load_config()
    if not TOKEN or TOKEN == '':
        print("ОШИБКА: Токен GITLAB_TOKEN не найден в .litconfig")
        return

    headers = {'Private-Token': TOKEN}

    # Получаем информацию о текущем пользователе
    response = requests.get(f'{GITLAB_URL}/api/v4/user', headers=headers)
    response.raise_for_status()
    user = response.json()
    username = user['username']
    #TODO добавить логику в случае пустого конфига gitlab login
    username = TARGET_USER

    # Рассчитываем дату DAYS дней назад
    since_datetime = datetime.now() - timedelta(days=DAYS)
    since_date_iso = since_datetime.isoformat()

    print(f'Поиск проектов за {DAYS} дней...', end="", flush=True)

    # Получаем все проекты пользователя
    projects = []
    page = 1
    while True:
        response = requests.get(
            f'{GITLAB_URL}/api/v4/projects',
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
                print(f'\rПоиск проектов за {DAYS} дней... {len(projects)}', end="", flush=True)

            except (KeyError, TypeError, ValueError) as e:
                print(f"\nОшибка обработки проекта {project.get('id')}: {str(e)}\n")

        page += 1

    print(f'\rПоиск коммитов за {DAYS} дней...', end="", flush=True)

    # Собираем коммиты из всех проектов
    comments = []
    for index, project in enumerate(projects, 1):
        # Выводим прогресс обработки
        print(f'\rПоиск коммитов за {DAYS} дней... {index}/{len(projects)}', end='', flush=True)

        project_id = project['id']
        page = 1
        while True:
            try:
                response = requests.get(
                    f'{GITLAB_URL}/api/v4/projects/{project_id}/repository/commits',
                    headers=headers,
                    params={
                        'since': since_date_iso,
                        # 'until': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),  # Добавляем верхнюю границу
                        'author_username': username,
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
                    # Проверяем и автора и коммиттера
                    commit_author = commit['author_email'].split("@")[0]
                    commit_committer = commit['committer_email'].split("@")[0]

                    if len(commit['message']) > 0 and (
                            commit_author.lower() == username.lower() or commit_committer.lower() == username.lower()):
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

    print(f'\rНайдено {useful_commits} пригодных коммитов из {len(comments)} в {len(sorted_tasks)} репозиториях за авторством {username}')

    save_commits(sorted_tasks)
