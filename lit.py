import os
import argparse
import shlex
import re
import subprocess
import tomllib
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.patch_stdout import patch_stdout
from init import init_config
from parser import pars_store
from import_jira import load_tasks_from_jira
from import_gitlab import load_commits_from_gitlab
from push import add_worklog, jira_connect
from utils import sort_key, load_dict, safe_split

#TODO Конфигурация дублируется, вынести в отдельный код
LIT_DIR = os.path.join(os.path.expanduser("~"), ".lit")
os.makedirs(LIT_DIR, exist_ok=True)
LIT_STORE = os.path.join(LIT_DIR, ".litstore")
LIT_HISTORY = os.path.join(LIT_DIR, ".lithistory")
COMMITS_FILE = os.path.join(LIT_DIR, "commits.json")
TASKS_FILE = os.path.join(LIT_DIR, "tasks.json")

COMMITS = load_dict(COMMITS_FILE)
TASKS = load_dict(TASKS_FILE)

class WorklogCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = safe_split(document.text_before_cursor)
        add_arg_params = {
            '-d': 'Дата (дд.мм.гггг)',
            '-t': 'Время (чч:мм)'
        }

        # Автодополнение команд
        if len(text) <= 1 and not document.text_before_cursor.endswith(" "):
            current_input_part = text[0] if text else ''
            current_input = current_input_part.lower()
            for cmd in ['add', 'status', 'push', 'pull', 'edit', 'init']:
                if cmd.startswith(current_input):
                    yield Completion(
                        cmd,
                        start_position=-len(current_input_part),
                        display=cmd
                    )
            return

        # Автодополнение для команды add
        if text[0] == 'add':
            args_after_add = text[1:]
            num_args = len(args_after_add)

            if num_args == 0:
                # Предлагаем все коды задач
                for task in TASKS:
                    yield Completion(task, start_position=0, display=f"{task} - {TASKS[task]}")

            elif num_args == 1 and not document.text_before_cursor.endswith(" "):
                # Ищем в номере задачи и названии (регистронезависимо)
                user_input = args_after_add[0].lower()
                for task in TASKS:
                    task_lower = task.lower()
                    desc_lower = TASKS[task].lower()

                    # Проверяем совпадение в коде или описании
                    if user_input in task_lower or user_input in desc_lower:
                        display_text = f"{task} - {TASKS[task]}"
                        # Вычисляем смещение для подсветки
                        start_pos = -len(args_after_add[0])
                        yield Completion(
                            task,
                            start_position=start_pos,
                            display=display_text,
                            display_meta=f"Найдено в {'коде' if user_input in task_lower else 'описании'}"
                        )

            elif num_args == 1:
                # Автодополнение для часов
                suggestions = ["1", "30m", "2h", "1d", "4h", "3h", "'1h 30m'", "15m", "20m", "10m"]
                for suggestion in suggestions:
                    yield Completion(suggestion, start_position=0)

            elif num_args == 2:
                # Автодополнение для сообщения:
                task_code = args_after_add[0]
                commit_part = args_after_add[2] if num_args >= 3 else ''
                commit_messages = COMMITS.get(task_code, [])
                for commit in commit_messages:
                    yield Completion(f"'{commit}'", start_position=-len(commit_part), display=commit)

            elif num_args == 3:
                # Предлагаем все коды задач
                for param in add_arg_params:
                    yield Completion(param, start_position=0, display=f"{param} - {add_arg_params[param]}")

            # Обработка флагов (-d, -t)
            else:
                # Если последний аргумент начинается с '-', предлагаем параметры
                if args_after_add and args_after_add[-1].startswith('-'):
                    current_param = args_after_add[-1]
                    for param in add_arg_params:
                        if param.startswith(current_param):
                            yield Completion(
                                param,
                                start_position=-len(current_param),
                                display=f"{param} - {add_arg_params[param]}"
                            )
            return

        # Автодополнение для команды pull
        if text[0] == 'pull':
            args_after_add = text[1:]
            num_args = len(args_after_add)

            if num_args == 0:
                for key in ['--jira', '--gitlab']:
                    yield Completion(key, start_position=0)

        # Другие команды (status, push) не требуют автодополнения
        return

class WorklogManager:
    def __init__(self):
        self.entries = []
        self.history = []
        self._load()

    def _load(self):
        if os.path.exists(LIT_STORE):
            try:
                with open(LIT_STORE, 'r', encoding='utf-8') as f:
                    self.entries = [line.strip() for line in f.readlines() if line.strip()]
            except Exception as e:
                print(f"Ошибка при загрузке: {e}")

    def _save(self):
        try:
            with open(LIT_STORE, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.entries) + "\n")  # Добавить + "\n"
            # print("Файл успешно сохранён.")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def _history(self):
        try:
            with open(LIT_HISTORY, 'a', encoding='utf-8') as f:
                f.write("\n".join(self.history) + "\n")  # Добавить + "\n"
            # print("Файл успешно сохранён.")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def add_entry(self, args):
        if isinstance(args, dict):  # Если аргументы пришли из CLI
            opts = argparse.Namespace(**args)
        else:  # Если из интерактивного режима
            parser = argparse.ArgumentParser(prog='lit add', exit_on_error=False)
            self._configure_add_parser(parser)
            opts = parser.parse_args(args)

        try:
            opts.code = opts.code.upper()
            input_time = datetime.strptime(opts.time, "%H:%M").time()

            # Проверка формата кода задачи
            if not re.match(r'^[A-Z]{2,}-\d+$', opts.code):
                raise ValueError(f"Неверный формат кода задачи: {opts.code}. Ожидается формат: ABC-123")

            # Проверка существования задачи в системе
            if opts.code not in TASKS:
                print(f"⚠️ Внимание: Задача {opts.code} не найдена в системе. Запись будет создана с ручным вводом!")

            if input_time > dt_time(19, 0):
                print(f"⚠️ Внимание: В задаче {opts.code} указано время начала {opts.time} для даты {opts.date}!")
                print(f"             Это может вызвать потенциальные проблемы в случае нестандартных часовых поясов!")
                print(f"             Используйте ключ -t для указания начального времени. Например: -t 10:00 ")

            if input_time < dt_time(5, 0):
                print(f"⚠️ Внимание: В задаче {opts.code} указано время начала {opts.time} для даты {opts.date}!")

            pattern = r'(\d+(?:[.,]\d+)?)([dhmDHM])?'
            matches = re.findall(pattern, opts.hours)

            if not matches:
                raise ValueError("Неверный формат количества времени. Ожидается, например, '1h 15m' или '8'.")

            hours = 0.0
            hours_str = ''
            for value, unit in matches:
                # Если суффикс не указан, считаем, что это часы.
                unit = unit if unit else 'h'
                num = float(value.replace(',', '.'))
                if unit.lower() == 'd':
                    hours += num * 8
                elif unit.lower() == 'h':
                    hours += num
                elif unit.lower() == 'm':
                    hours += num / 60

                hours_str += f'{value}{unit} '

            opts.hours = hours_str.strip().replace('.', ',')

            # Расчет времени окончания
            start_time = datetime.strptime(f"{opts.date} {opts.time}", "%d.%m.%Y %H:%M")
            end_time = start_time + timedelta(hours=hours)

            # Форматирование записи
            entry = (
                f"{opts.date} [{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}] "
                f"{opts.code} {opts.hours} `{opts.message}`"
            )
            self.entries.append(entry)
            self._save()

        except Exception as e:
            print(f"⛔ Ошибка: {str(e)}")

    def show_status(self):
        if not self.entries:
            print("Нет подготовленных записей.")
            return

        store_dist = pars_store(self.entries)

        sorted_data = sorted(store_dist, key=sort_key)

        print("\nПодготовленные записи:")

        current_date = None
        for entry in sorted_data:
            if entry['disabled'] is None:
                date_part = entry['date']

                # Проверяем изменилась ли дата
                if date_part != current_date:
                    print(f"\n{date_part}")
                    current_date = date_part

                print(f"  {entry['log'].split(date_part)[1].strip('\n')}")

        print("\nНе будут оправляться:")

        current_date = None
        for entry in sorted_data:
            if entry['disabled'] is not None:
                date_part = entry['date']

                # Проверяем изменилась ли дата
                if date_part != current_date:
                    print(f"\n{date_part}")
                    current_date = date_part

                print(f"  {entry['log'].split(date_part)[1].strip('\n')}")

    def push_entries(self):
        if not self.entries:
            print("Нет записей для отправки.")
            return

        self.show_status()
        session = PromptSession()
        confirm = session.prompt("\nВы уверены что хотите отправить эти записи? [y/N]: ").strip().lower()

        if confirm == 'y':
            print("\nОтправка записей в Jira...")

            store_dist = pars_store(self.entries)

            errors = []
            saved = []

            jira = jira_connect()

            for log in store_dist:
                if not log['disabled']:
                    id, err = add_worklog(jira, log['code'], log['duration'], log['message'], log['date'], log['start'])
                    if not id:
                        errors.append(f'# {log['log'].strip('\n')} # {err}')
                    else:
                        saved.append(f'{log['log'].strip('\n')} # {id}')
                else:
                    errors.append(f'{log['log'].strip('\n')}')

            self.entries = errors
            self.history = saved
            self._save()
            self._history()
            print(f"Записей успешно отправлено: {len(saved)}")
            print(f"Записей неотправленных записей: {len(errors)}")
        else:
            print("Отмена отправки.")

    @staticmethod
    def _configure_add_parser(parser):
        """Настройка парсера для команды add."""
        parser.add_argument('code', help='Код задачи (например, TASK-123)')
        parser.add_argument('hours', help='Количество часов или минут (например, 15m)')
        parser.add_argument('message', help='Сообщение')
        parser.add_argument('-d', '--date',
                            default=datetime.now().strftime('%d.%m.%Y'),
                            help='Дата (дд.мм.гггг)')
        parser.add_argument('-t', '--time',
                            default=datetime.now().strftime('%H:%M'),
                            help='Время (чч:мм)')

    def edit_entries(self):
        """Открыть файл .litstore в редакторе"""
        # Определяем редактор по умолчанию для Windows
        if os.name == 'nt':
            default_editor = 'notepad'
        else:
            default_editor = 'vim'

        editor = os.environ.get('EDITOR') or os.environ.get('VISUAL') or default_editor

        try:
            # Создаем файл если его нет
            if not os.path.exists(LIT_STORE):
                open(LIT_STORE, 'w').close()

            # Для Notepad в Windows используем shell=True
            if os.name == 'nt' and 'notepad' in editor.lower():
                subprocess.run(f'"{editor}" "{LIT_STORE}"', shell=True, check=True)
            else:
                subprocess.run([editor, LIT_STORE], check=True)

            # Перезагружаем данные в любом случае
            self._load()
            print("✓ Изменения применены")

        except subprocess.CalledProcessError as e:
            print(f"⚠ Ошибка редактора: {str(e)}")
            if os.name == 'nt':
                print("Попробуйте установить редактор (например Notepad++) и добавить его в PATH")
        except Exception as e:
            print(f"⚠ Ошибка: {str(e)}")

    def pull_entries(self, args=None, jira=None, gitlab=None):
        """Загружает задачи из Jira и/или коммиты из GitLab."""
        # Определяем, что загружать, на основе переданных аргументов
        if jira is not None or gitlab is not None:
            # Вызов из CLI с ключевыми аргументами
            load_jira = jira
            load_gitlab = gitlab
        else:
            # Вызов из интерактивного режима: парсим аргументы
            parser = argparse.ArgumentParser(prog='lit pull', exit_on_error=False)
            parser.add_argument('-j', '--jira', action='store_true', help='Загрузить задачи из Jira')
            parser.add_argument('-g', '--gitlab', action='store_true', help='Загрузить коммиты из GitLab')
            try:
                opts = parser.parse_args(args or [])
            except SystemExit:
                # В случае ошибки парсинга (например, неверный аргумент)
                return
            load_jira = opts.jira
            load_gitlab = opts.gitlab

        # Если ни один флаг не указан, загружаем оба источника
        if not load_jira and not load_gitlab:
            load_jira = True
            load_gitlab = True

        # Загрузка данных
        if load_jira:
            load_tasks_from_jira()
        if load_gitlab:
            load_commits_from_gitlab()

    def init_config(self):
        """Обертка для инициализации конфига"""
        init_config()


def get_version():
    """Получить версию из pyproject.toml"""
    try:
        path = Path(__file__).parent / "pyproject.toml"
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except (KeyError, FileNotFoundError):
        return "0.0.0-dev"


def main():
    welcome_art = r"""
    ┌LIT>────────┐  Консольная утилита для удобного
    │ TSK 8h ─○─ │  управления рабочими логами     
    └─────────╲╲─┘  с интеграцией Jira и GitLab     
    """

    print("\033[36m" + welcome_art + "\033[0m")  # Цвет cyan
    manager = WorklogManager()
    session = PromptSession(completer=WorklogCompleter())

    with patch_stdout():
        while True:
            try:
                user_input = session.prompt('lit> ').strip()
                if not user_input:
                    continue

                args = shlex.split(user_input)
                command = args[0]

                if command == 'add':
                    manager.add_entry(args[1:])
                elif command == 'status':
                    manager.show_status()
                elif command == 'push':
                    manager.push_entries()
                elif command == 'pull':
                    manager.pull_entries(args[1:])
                elif command == 'edit':
                    manager.edit_entries()
                elif command == 'init':
                    manager.init_config()
                else:
                    print("Неизвестная команда")

            except (KeyboardInterrupt, EOFError):
                print("\nЗавершение работы.")
                break
            except Exception as e:
                print(f"Ошибка: {str(e)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Утилита для работы с ворклогами.")
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f"lit v{get_version()}",
        help="Показать версию и выйти"
    )

    # Парсер для команды add
    add_parser = subparsers.add_parser('add', help='Добавить запись в ворклог')
    WorklogManager._configure_add_parser(add_parser)

    # Парсер для команды status
    subparsers.add_parser('status', help='Показать статус ворклога')

    # Парсер для команды push
    subparsers.add_parser('push', help='Отправить записи в Jira')

    # Изменённый блок для команды pull
    pull_parser = subparsers.add_parser('pull', help='Получить задачи из Jira и коммиты из gitlab')
    pull_parser.add_argument('-j', '--jira', action='store_true', help='Загрузить задачи из Jira')
    pull_parser.add_argument('-g', '--gitlab', action='store_true', help='Загрузить коммиты из GitLab')

    # Парсер для команды edit
    subparsers.add_parser('edit', help='Редактировать файл ворклога')

    # Парсер для команды init
    subparsers.add_parser('init', help='Настроить конфигурацию')

    args = parser.parse_args()
    manager = WorklogManager()

    if args.command == 'add':
        manager.add_entry(vars(args))
    elif args.command == 'status':
        manager.show_status()
    elif args.command == 'push':
        manager.push_entries()
    elif args.command == 'pull':
        manager.pull_entries(jira=args.jira, gitlab=args.gitlab)
    elif args.command == 'edit':
        manager.edit_entries()
    elif args.command == 'init':
        manager.init_config()
    else:
        main()
