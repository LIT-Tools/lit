from __future__ import annotations

from jira import JIRA, exceptions
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import os
import json
from config_manager import get_jira

#TODO В утилсы
def save_commits(data: dict):
    """Сохранение коммитов в файл с атомарной записью"""
    try:
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving commits: {str(e)}")

from constants import LIT_DIR, TASKS_FILE
os.makedirs(LIT_DIR, exist_ok=True)


def pars_error_jira(e: Exception) -> None:
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


def load_tasks_from_jira() -> None:
    config = get_jira()
    AUTH = (config["login"], config["pass"])
    url = config["url"]
    days = config["days"]
    
    #TODO вынести в отдельный конектор
    try:
        jira = JIRA(
            server=url,
            basic_auth=AUTH,
            options={
                'server': url,
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
    first_day_previous_month = today - timedelta(days=days)

    date_format = '%Y-%m-%d'
    start_date = first_day_previous_month.strftime(date_format)
    end_date = today.strftime(date_format)

    # Формируем JQL запросы
    jql_assignee = f'assignee = "{TARGET_USER}" AND updated >= "{start_date}"'
    jql_worklog = f'worklogAuthor = "{TARGET_USER}" AND worklogDate >= "{start_date}"'

    def get_all_issues(jql_query: str) -> list:
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
