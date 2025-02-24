import os
import argparse
from datetime import datetime, timedelta
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.patch_stdout import patch_stdout

# Конфигурация
LOG_FILE = os.path.join(os.path.expanduser("~"), ".litlog")
TASKS = {
    'SOGAZ-123': 'добавить кнопку',
    'SOGAZ-44': 'настройка сборки фронта',
    'SOGAZ-1752': 'Скрыть страницу О компании',
}


class WorklogCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.split()

        # Автодополнение команд
        if len(text) == 0:
            for cmd in ['add', 'status', 'push']:
                yield Completion(cmd, start_position=0, display=cmd)
            return

        # Автодополнение параметров для add
        if text[0] == 'add':
            params = {
                '-c': 'Код задачи',
                '-l': 'Часы',
                '-m': 'Сообщение',
                '-d': 'Дата (дд.мм.гггг)',
                '-t': 'Время (чч:мм)'
            }

            # Предлагаем параметры или значения
            if len(text) == 1:
                for param, desc in params.items():
                    yield Completion(param, start_position=0, display=f"{param} - {desc}")

            # Автодополнение кодов задач
            if '-c' in text:
                task_part = text[-1].upper()
                for task in TASKS:
                    if task.startswith(task_part):
                        yield Completion(task, start_position=-len(task_part), display=f"{task} - {TASKS[task]}")


class WorklogManager:
    def __init__(self):
        self.entries = []
        self._load()

    def _load(self):
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    self.entries = [line.strip() for line in f.readlines() if line.strip()]
            except Exception as e:
                print(f"Ошибка при загрузке: {e}")

    def _save(self):
        try:
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.entries) + "\n")  # Добавить + "\n"
            # print("Файл успешно сохранён.")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def add_entry(self, args):
        parser = argparse.ArgumentParser(prog='lit add', exit_on_error=False)
        self._configure_add_parser(parser)

        try:
            # Обработка позиционных аргументов
            if len(args) >= 3 and not args[0].startswith('-'):
                args = ['-c', args[0], '-l', args[1], '-m', ' '.join(args[2:])]

            opts = parser.parse_args(args)

            # Валидация
            if opts.code not in TASKS:
                raise ValueError(f"Неизвестный код задачи: {opts.code}")

            # Расчет времени окончания
            start_time = datetime.strptime(f"{opts.date} {opts.time}", "%d.%m.%Y %H:%M")
            end_time = start_time + timedelta(hours=opts.l)

            # Форматирование записи
            entry = (
                f"{opts.date} [{opts.time} - {end_time.strftime('%H:%M')}] "
                f"{opts.code} {opts.l:.1f}h `{opts.message}`"
            )
            self.entries.append(entry)
            self._save()
            # print(f"Запись добавлена! Файл: {LOG_FILE}")

        except Exception as e:
            print(f"Ошибка: {str(e)}")

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
        parser.add_argument('-c', '--code', required=True, help='Код задачи')
        parser.add_argument('-l', type=float, required=True, help='Количество часов')
        parser.add_argument('-m', '--message', required=True, help='Сообщение')
        parser.add_argument('-d', '--date', default=datetime.now().strftime('%d.%m.%Y'), help='Дата (дд.мм.гггг)')
        parser.add_argument('-t', '--time', default=datetime.now().strftime('%H:%M'), help='Время (чч:мм)')


def main():
    manager = WorklogManager()
    session = PromptSession(completer=WorklogCompleter())

    with patch_stdout():
        while True:
            try:
                user_input = session.prompt('lit> ').strip()
                if not user_input:
                    continue

                args = user_input.split()
                command = args[0]

                if command == 'add':
                    manager.add_entry(args[1:])
                elif command == 'status':
                    manager.show_status()
                elif command == 'push':
                    manager.push_entries()
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

    args = parser.parse_args()
    manager = WorklogManager()

    if args.command == 'add':
        # Преобразуем Namespace в список аргументов
        add_args = []
        for key, value in vars(args).items():
            if key == 'command':
                continue
            if key == 'l':
                add_args.extend(['-l', str(value)])
            else:
                add_args.extend([f'--{key}', str(value)])
        manager.add_entry(add_args)
    elif args.command == 'status':
        manager.show_status()
    elif args.command == 'push':
        manager.push_entries()
    else:
        main()