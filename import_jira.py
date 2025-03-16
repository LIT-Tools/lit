from jira import JIRA, exceptions
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import os
import json
import configparser

#TODO В утилсы
def save_commits(data: dict):
    """Сохранение коммитов в файл с атомарной записью"""
    try:
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving commits: {str(e)}")

#TODO Конфигурация дублируется, вынести в отдельный код
LIT_DIR = os.path.join(os.path.expanduser("~"), ".lit")
os.makedirs(LIT_DIR, exist_ok=True)
TASKS_FILE = os.path.join(LIT_DIR, "tasks.json")
CONFIG_FILE = os.path.join(LIT_DIR, ".litconfig")

JIRA_URL = ''
# USER_EMAIL = config.get('jira', 'email')
PASS = ''
TARGET_USER = ''
DAYS = ''

def load_config():
    global JIRA_URL, PASS, TARGET_USER, DAYS
    # Создаем конфиг-парсер с сохранением регистра
    config = configparser.RawConfigParser()
    config.optionxform = lambda option: option  # Отключаем авто-преобразование в lowercase
    config.read(CONFIG_FILE)

    JIRA_URL = config.get('jira', 'url')
    PASS = config.get('jira', 'pass')
    TARGET_USER = config.get('jira', 'login')
    DAYS = int(config.get('jira', 'days'))

#TODO вынести в отдельный конектор или утилсы
def pars_error_jira(e):
    soup = BeautifulSoup(e.text, 'html.parser')
    error_div = soup.find('div', class_='aui-message-warning')

    if error_div:
        # Извлекаем все текстовые элементы ошибки
        error_messages = []
        for p in error_div.find_all('p'):
            if p.a:  # Пропускаем параграфы со ссылками
                continue
            error_messages.append(p.get_text(strip=True))

        print("Ошибка подключения к Jira:")
        print('\n'.join(error_messages) if error_messages else 'Неизвестная ошибка')
    else:
        print(f"HTTP ошибка {e.status_code}: {e.text}")


def load_tasks_from_jira():
    load_config()
    #TODO вынести в отдельный конектор
    AUTH = (TARGET_USER, PASS)
    # Создаем клиент Jira с базовой аутентификацией
    try:
        jira = JIRA(
            server=JIRA_URL,
            basic_auth=AUTH,
            options={
                'server': JIRA_URL,
                'rest_api_version': '2',  # Явно указываем версию API
                'verify': True
            },
            timeout=20
        )
    except exceptions.JIRAError as e:
        pars_error_jira(e)
        exit()

    # Проверка подключения
    try:
        print(f"Успешное подключение к Jira {jira.server_info()['version']}")
        print(f"Авторизованы как: {jira.current_user()}")
    except exceptions.JIRAError as e:
        pars_error_jira(e)
        exit()

    # Рассчитываем даты за прошлый месяц
    today = datetime.today()
    first_day_previous_month = today - timedelta(days=DAYS)

    date_format = '%Y-%m-%d'
    start_date = first_day_previous_month.strftime(date_format)
    end_date = today.strftime(date_format)

    # Формируем JQL запросы
    jql_assignee = f'assignee = "{TARGET_USER}" AND updated >= "{start_date}" AND updated <= "{end_date}"'
    jql_worklog = f'worklogAuthor = "{TARGET_USER}" AND worklogDate >= "{start_date}" AND worklogDate <= "{end_date}"'

    def get_all_issues(jql_query):
        """Получаем все задачи по JQL-запросу с пагинацией"""
        issues = []
        start_at = 0
        max_results = 50

        while True:
            try:
                chunk = jira.search_issues(
                    jql_query,
                    startAt=start_at,
                    maxResults=max_results,
                    fields='key,summary,status,assignee'
                )
            except Exception as e:
                print(f"Ошибка при выполнении запроса: {e}")
                break

            issues.extend(chunk)
            start_at += len(chunk)
            if len(chunk) < max_results:
                break
        return issues

    # Получаем задачи
    print("Поиск задач...", end="", flush=True)
    assignee_issues = get_all_issues(jql_assignee)
    print(f"\rНайдено задач: {len(assignee_issues)}")  # Пробелы для затирания старого текста

    print("Поиск задач по ворклогам...", end="", flush=True)
    worklog_issues = get_all_issues(jql_worklog)
    print(f"\rВ задач логал: {len(worklog_issues)}" + " " * 30)

    # Объединяем и удаляем дубликаты
    all_issues = assignee_issues + worklog_issues
    unique_issues = {issue.key: issue for issue in all_issues}.values()

    # Выводим результаты
    print(f"Всего уникальных задач: {len(unique_issues)}")

    TASKS = {}
    tasks = {}
    for idx, issue in enumerate(unique_issues, 1):
        TASKS = {
            issue.key: issue.fields.summary
            for issue in unique_issues
        }

    save_commits(TASKS)
