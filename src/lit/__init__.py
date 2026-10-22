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
from lit.init import init_config
from lit.parser import pars_store
from lit.integrations.jira import load_tasks_from_jira
from lit.integrations.gitlab import load_commits_from_gitlab
from lit.integrations.jira_push import add_worklog, jira_connect
from lit.utils import sort_key, load_dict, safe_split
from lit.core.worklog_manager import WorklogManager

from lit.config_manager import get_user
from lit.constants import (
    LIT_DIR, LIT_STORE, LIT_HISTORY,
    CONFIG_FILE, COMMITS_FILE, TASKS_FILE,
)

COMMITS = load_dict(COMMITS_FILE)
TASKS = load_dict(TASKS_FILE)
CUSTOM_EDITOR = ''

def load_config(path=None):
    """Алиас для совместимости."""
    global CUSTOM_EDITOR
    user = get_user()
    CUSTOM_EDITOR = user["editor"]
    return user

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

def get_version():
    """Получить версию из pyproject.toml"""
    try:
        path = Path(__file__).parent / "pyproject.toml"
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except (KeyError, FileNotFoundError):
        return "0.0.0-dev"


def main(parser):
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

                if user_input in ['-h', '--help']:
                    parser.print_help()
                    continue

                if user_input in ['-v', '--version']:
                    print(f"lit v{get_version()}")
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

def create_argument_parser():
    """Создает и возвращает настроенный парсер аргументов"""
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

    return parser

def process_arguments(args=None):
    """Обрабатывает аргументы командной строки"""
    parser = create_argument_parser()
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
        main(parser)

def cli() -> None:
    """Entry point for the console script (``lit``)."""
    process_arguments()


