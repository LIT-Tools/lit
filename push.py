from jira import JIRA
from jira.exceptions import JIRAError
from datetime import datetime
from tzlocal import get_localzone
import os
import configparser

# TODO Конфигурация дублируется, вынести в отдельный код
LIT_DIR = os.path.join(os.path.expanduser("~"), ".lit")
os.makedirs(LIT_DIR, exist_ok=True)
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

# TODO вынести в отдельный конектор
def jira_connect():
    load_config()
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

def add_worklog(jira, issue, time_spent, comment, day, time):

    start_time = datetime.strptime(f"{day} {time}", "%d.%m.%Y %H:%M").replace(tzinfo=get_localzone())
    try:
        id = jira.add_worklog(issue, timeSpent=time_spent, comment=comment, started=start_time)
    except JIRAError as e:
        return None, e.text

    except Exception as e:
        return None, str(e)
    else:
        return id, None
