"""Бизнес-логика управления ворклогами."""
import argparse
import os
import re
import subprocess
from datetime import datetime, timedelta, time as dt_time
from constants import LIT_HISTORY, LIT_STORE
from parser import pars_store
from utils import sort_key
from prompt_toolkit import PromptSession

CUSTOM_EDITOR = ''

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
                f.write("\n".join(self.entries) + "\n")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def _history(self):
        try:
            with open(LIT_HISTORY, 'a', encoding='utf-8') as f:
                f.write("\n".join(self.history) + "\n")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def add_entry(self, args):
        from lit import TASKS
        if isinstance(args, dict):
            opts = argparse.Namespace(**args)
        else:
            parser = argparse.ArgumentParser(prog='lit add', exit_on_error=False)
            self._configure_add_parser(parser)
            opts = parser.parse_args(args)
        try:
            opts.code = opts.code.upper()
            input_time = datetime.strptime(opts.time, "%H:%M").time()
            if not re.match(r'^[A-Z]{2,}-\d+$', opts.code):
                raise ValueError(f"Неверный формат кода задачи: {opts.code}. Ожидается формат: ABC-123")
            if opts.code not in TASKS:
                print(f"⚠️ Внимание: Задача {opts.code} не найдена в системе. Запись будет создана с ручным вводом!")
            if input_time > dt_time(19, 0):
                print(f"⚠️ Внимание: В задаче {opts.code} указано время начала {opts.time} для даты {opts.date}!")
            if input_time < dt_time(5, 0):
                print(f"⚠️ Внимание: В задаче {opts.code} указано время начала {opts.time} для даты {opts.date}!")
            pattern = r'(\d+(?:[.,]\d+)?)([dhmDHM])?'
            matches = re.findall(pattern, opts.hours)
            if not matches:
                raise ValueError("Неверный формат количества времени. Ожидается, например, '1h 15m' или '8'.")
            hours = 0.0
            hours_str = ''
            for value, unit in matches:
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
            try:
                date_obj = datetime.strptime(opts.date, "%d.%m.%Y")
            except ValueError:
                print(
                    f"⛔ Ошибка: Неверная дата '{opts.date}'. "
                    f"Ожидается формат дд.мм.гггг (например, 25.12.2023)."
                )
                return
            formatted_date = date_obj.strftime("%d.%m.%Y")
            start_time = datetime.strptime(f"{opts.date} {opts.time}", "%d.%m.%Y %H:%M")
            end_time = start_time + timedelta(hours=hours)
            message = opts.message.replace('\n', '\\n')
            entry = (f"{formatted_date} [{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}] " f"{opts.code} {opts.hours} `{message}`")
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
                if date_part != current_date:
                    print(f"\n{date_part}")
                    current_date = date_part
                print(f"  {entry['log'].split(date_part)[1].strip('\n')}")
        print("\nНе будут оправляться:")
        current_date = None
        for entry in sorted_data:
            if entry['disabled'] is not None:
                date_part = entry['date']
                if date_part != current_date:
                    print(f"\n{date_part}")
                    current_date = date_part
                print(f"  {entry['log'].split(date_part)[1].strip('\n')}")

    def push_entries(self):
        from lit import add_worklog, jira_connect
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
                    message = log['message'].replace("\\n", '\n')
                    id, err = add_worklog(jira, log['code'], log['duration'], message, log['date'], log['start'])
                    if not id:
                        errors.append(f"# {log['log'].strip('\n')} # {err}")
                    else:
                        saved.append(f"{log['log'].strip('\n')} # {id}")
                else:
                    errors.append(f"{log['log'].strip('\n')}")
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
        parser.add_argument('code', help='Код задачи (например, TASK-123)')
        parser.add_argument('hours', help='Количество часов или минут (например, 15m)')
        parser.add_argument('message', help='Сообщение')
        parser.add_argument('-d', '--date', default=datetime.now().strftime('%d.%m.%Y'), help='Дата (дд.мм.гггг)')
        parser.add_argument('-t', '--time', default=datetime.now().strftime('%H:%M'), help='Время (чч:мм)')

    def edit_entries(self):
        try:
            from lit import CUSTOM_EDITOR
        except ImportError:
            CUSTOM_EDITOR = ''
        if os.name == 'nt':
            default_editor = 'notepad'
        else:
            default_editor = 'vim'
        editor = CUSTOM_EDITOR or os.environ.get('EDITOR') or os.environ.get('VISUAL') or default_editor
        try:
            cmd = [editor, LIT_STORE]
            print(cmd)
            subprocess.run(cmd, shell=(os.name == 'nt'), check=True, encoding='utf-8')
            self._load()
            print("✓ Изменения применены")
        except subprocess.CalledProcessError as e:
            print(f"⚠ Ошибка редактора: {str(e)}")
            if os.name == 'nt':
                print("Попробуйте установить редактор (например Notepad++) и добавить его в PATH")
        except Exception as e:
            print(f"⚠ Ошибка: {str(e)}")

    def pull_entries(self, args=None, jira=None, gitlab=None):
        from lit import load_commits_from_gitlab, load_tasks_from_jira
        if jira is not None or gitlab is not None:
            load_jira = jira
            load_gitlab = gitlab
        else:
            parser = argparse.ArgumentParser(prog='lit pull', exit_on_error=False)
            parser.add_argument('-j', '--jira', action='store_true', help='Загрузить задачи из Jira')
            parser.add_argument('-g', '--gitlab', action='store_true', help='Загрузить коммиты из GitLab')
            try:
                opts = parser.parse_args(args or [])
            except SystemExit:
                return
            load_jira = opts.jira
            load_gitlab = opts.gitlab
        if not load_jira and not load_gitlab:
            load_jira = True
            load_gitlab = True
        if load_jira:
            load_tasks_from_jira()
        if load_gitlab:
            load_commits_from_gitlab()

    def init_config(self):
        from lit import init_config
        init_config()
