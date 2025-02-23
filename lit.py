from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.patch_stdout import patch_stdout
import sys

TASKS = {
    'SOGAZ-123': 'добавить кнопку',
    'SOGAZ-44': 'настройка сборки фронта',
    'SOGAZ-1752': 'Скрыть страницу О компании',
}

class TaskCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.upper()
        for task_id, desc in TASKS.items():
            if text in task_id.upper():
                yield Completion(
                    task_id,
                    start_position=-len(text),
                    display=f"{task_id} - {desc}",
                )

def main():
    session = PromptSession(completer=TaskCompleter())
    with patch_stdout():
        try:
            task = session.prompt('lit ')
            print(f"Выбрана задача: {task}")
        except (KeyboardInterrupt, EOFError):
            print("\nЗавершение работы.")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        main()
    else:
        task = sys.argv[1]
        if task in TASKS:
            print(f"Задача: {task} - {TASKS[task]}")
        else:
            matches = [t for t in TASKS if task.upper() in t.upper()]
            if matches:
                print("Найдены задачи:")
                for t in matches:
                    print(f"{t} - {TASKS[t]}")
            else:
                print("Задачи не найдены.")