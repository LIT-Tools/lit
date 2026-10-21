from __future__ import annotations

from jira import JIRA
from jira.exceptions import JIRAError
from datetime import datetime
from tzlocal import get_localzone
import os
from config_manager import get_jira
from constants import LIT_DIR

os.makedirs(LIT_DIR, exist_ok=True)


def jira_connect() -> JIRA:
    config = get_jira()
    AUTH = (config["login"], config["pass"])
    url = config["url"]
    days = config["days"]
    
    # Создаем клиент Jira с базовой аутентификацией
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
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        exit()

    # Проверка подключения
    try:
        print(f"Успешное подключение к Jira {jira.server_info()['version']}")
        print(f"Авторизованы как: {jira.current_user()}")
    except Exception as e:
        print(f"Ошибка проверки подключения: {e}")
        exit()

    return jira

def add_worklog(jira: JIRA, issue: str, time_spent: str, comment: str, day: str, time: str) -> tuple[str | None, str | None]:

    start_time = datetime.strptime(f"{day} {time}", "%d.%m.%Y %H:%M").replace(tzinfo=get_localzone())
    try:
        id = jira.add_worklog(issue, timeSpent=time_spent, comment=comment, started=start_time)
    except JIRAError as e:
        return None, e.text

    except Exception as e:
        return None, str(e)
    else:
        return id, None
