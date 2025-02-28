import os
import argparse
import shlex
import re
import subprocess
import json
from datetime import datetime, timedelta
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.patch_stdout import patch_stdout

# Конфигурация
LIT_DIR = os.path.join(os.path.expanduser("~"), ".lit")
os.makedirs(LIT_DIR, exist_ok=True)
LIT_STORE = os.path.join(LIT_DIR, ".litstore")

# Путь к файлу с коммитами
COMMITS_FILE = os.path.join(LIT_DIR, "commits.json")

TASKS = {
    'TASK-123': 'добавить кнопку',
    'TASK-44': 'настройка сборки фронта',
    'TASK-1752': 'Скрыть страницу О компании',
    'BKWFM-1752': 'Настроит gRPC',
}

def load_commits() -> dict:
    """Загрузка коммитов из файла"""
    try:
        with open(COMMITS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Если файла нет - создаём с начальными данными
        return {}
    except json.JSONDecodeError:
        # Битый файл
        print(f"ERROR: Invalid JSON format.")
        return {}

COMMITS = load_commits()

class WorklogCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = shlex.split(document.text_before_cursor)
        params = {
            '-d': 'Дата (дд.мм.гггг)',
            '-t': 'Время (чч:мм)'
        }

        # Автодополнение команд
        if len(text) == 0:
            for cmd in ['add', 'status', 'push', 'edit']:
                yield Completion(cmd, start_position=0, display=cmd)
            return
        elif len(text) == 1 and not document.text_before_cursor.endswith(" "):
            for cmd in ['add', 'status', 'push', 'edit']:
                yield Completion(cmd, start_position=-len(text), display=cmd)
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
                # Предлагаем коды задач, начинающиеся с введенной части
                task_part = args_after_add[0].upper()
                for task in TASKS:
                    if task_part in task:
                        yield Completion(
                            task,
                            start_position=-len(task_part),
                            display=f"{task} - {TASKS[task]}"
                        )

            elif num_args == 1:
                # Автодополнение для часов
                suggestions = ["0.5", "1", "2", "4", "8"]
                for suggestion in suggestions:
                    yield Completion(suggestion, start_position=0, display=f"{suggestion} часов")

            elif num_args == 2:
                # Автодополнение для сообщения:
                task_code = args_after_add[0]
                commit_part = args_after_add[2] if num_args >= 3 else ''
                commit_messages = COMMITS.get(task_code, [])
                for commit in commit_messages:
                    yield Completion(f"'{commit}'", start_position=-len(commit_part),  display=commit)

            elif num_args == 3:
                # Предлагаем все коды задач
                for param in params:
                    yield Completion(param, start_position=0, display=f"{param} - {params[param]}")

            # Обработка флагов (-d, -t)
            else:
                # Если последний аргумент начинается с '-', предлагаем параметры
                if args_after_add and args_after_add[-1].startswith('-'):
                    current_param = args_after_add[-1]
                    for param in params:
                        if param.startswith(current_param):
                            yield Completion(
                                param,
                                start_position=-len(current_param),
                                display=f"{param} - {params[param]}"
                            )
            return

        # Другие команды (status, push) не требуют автодополнения
        return

class WorklogManager:
    def __init__(self):
        self.entries = []
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

    def add_entry(self, args):
        if isinstance(args, dict):  # Если аргументы пришли из CLI
            opts = argparse.Namespace(**args)
        else:  # Если из интерактивного режима
            parser = argparse.ArgumentParser(prog='lit add', exit_on_error=False)
            self._configure_add_parser(parser)
            opts = parser.parse_args(args)

        try:
            opts.code = opts.code.upper()

            # Проверка формата кода задачи
            if not re.match(r'^[A-Z]{2,}-\d+$', opts.code):
                raise ValueError(f"Неверный формат кода задачи: {opts.code}. Ожидается формат: ABC-123")

            # Проверка существования задачи в системе
            if opts.code not in TASKS:
                print(f"⚠️ Внимание: Задача {opts.code} не найдена в системе. Запись будет создана с ручным вводом!")

            # Расчет времени окончания
            start_time = datetime.strptime(f"{opts.date} {opts.time}", "%d.%m.%Y %H:%M")
            end_time = start_time + timedelta(hours=opts.hours)

            # Форматирование записи
            entry = (
                f"{opts.date} [{opts.time} - {end_time.strftime('%H:%M')}] "
                f"{opts.code} {opts.hours:.1f}h `{opts.message}`"
            )
            self.entries.append(entry)
            self._save()

        except Exception as e:
            print(f"⛔ Ошибка: {str(e)}")

    def show_status(self):
        if not self.entries:
            print("Нет подготовленных записей.")
            return

        current_date = None
        for entry in self.entries:
            date_part = entry.split()[0]
            if date_part != current_date:
                print(f"\n{date_part}")
                current_date = date_part
            print(f"  {entry.split('] ')[1]}")

    def push_entries(self):
        if not self.entries:
            print("Нет записей для отправки.")
            return

        print("\nПодготовленные записи:")
        self.show_status()
        confirm = input("\nВы уверены что хотите отправить эти записи? [y/N]: ").strip().lower()

        if confirm == 'y':
            print("\nОтправка записей в Jira...")
            # Здесь должна быть логика интеграции с Jira API
            self.entries = []
            self._save()
            print("Записи успешно отправлены!")
        else:
            print("Отмена отправки.")

    @staticmethod
    def _configure_add_parser(parser):
        """Настройка парсера для команды add."""
        parser.add_argument('code', help='Код задачи (например, TASK-123)')
        parser.add_argument('hours', type=float, help='Количество часов')
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

def main():
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
                elif command == 'edit':
                    manager.edit_entries()
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

    # Парсер для команды add
    add_parser = subparsers.add_parser('add', help='Добавить запись в ворклог')
    WorklogManager._configure_add_parser(add_parser)

    # Парсер для команды status
    subparsers.add_parser('status', help='Показать статус ворклога')

    # Парсер для команды push
    subparsers.add_parser('push', help='Отправить записи в Jira')

    # Парсер для команды edit
    subparsers.add_parser('edit', help='Редактировать файл ворклога')

    args = parser.parse_args()
    manager = WorklogManager()

    if args.command == 'add':
        manager.add_entry(vars(args))
    elif args.command == 'status':
        manager.show_status()
    elif args.command == 'push':
        manager.push_entries()
    elif args.command == 'edit':
        manager.edit_entries()
    else:
        main()