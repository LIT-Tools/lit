import unittest
from unittest.mock import patch, mock_open
from datetime import datetime
from lit import WorklogManager, WorklogCompleter, TASKS, LIT_STORE, LIT_HISTORY
from prompt_toolkit.document import Document

TASKS["TASK-123"] = "Test Task"

class TestWorklogManager(unittest.TestCase):
    def setUp(self):
        self.manager = WorklogManager()
        self.manager.entries = []

    def tearDown(self):
        pass  # Не требуется очистка реальных файлов

    class MockedDateTime(datetime):
        _fixed_time = datetime(2023, 1, 15, 14, 30)

        @classmethod
        def now(cls):
            return cls._fixed_time

        def __add__(self, delta):
            return self._fixed_time + delta

        def strftime(self, fmt):
            return self._fixed_time.strftime(fmt)

    @patch('lit.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_two_entries_success(self, mock_file, mock_datetime):
        mock_datetime.side_effect = lambda *args, **kw: self.MockedDateTime(*args, **kw)
        mock_datetime.now.return_value = self.MockedDateTime.now()
        mock_datetime.strptime.side_effect = lambda *args: datetime.strptime(*args)

        self.manager.add_entry(['TASK-123', '7', 'Описание работы'])
        self.manager.add_entry(['TASK-123', '1,5', 'Описание работы'])
        self.manager.add_entry(['TASK-123', '0.5', 'Описание работы'])
        self.manager.add_entry(['TASK-123', '15m', 'Описание работы', '-d', '20.02.2024', '-t', '10:00'])
        self.manager.add_entry(['TASK-123', '1d', 'Описание работы', '-d', '20.02.2024', '-t', '10:00'])

        expected_content = (
            "15.01.2023 [14:30 - 21:30] TASK-123 7h `Описание работы`\n"
            "15.01.2023 [14:30 - 16:00] TASK-123 1,5h `Описание работы`\n"
            "15.01.2023 [14:30 - 15:00] TASK-123 0,5h `Описание работы`\n"
            "20.02.2024 [10:00 - 10:15] TASK-123 15m `Описание работы`\n"
            "20.02.2024 [10:00 - 18:00] TASK-123 1d `Описание работы`\n"
        )
        mock_file().write.assert_called_with(expected_content)

    @patch('lit.add_worklog')  # Добавляем мок для add_worklog
    @patch('lit.jira_connect')  # Добавляем мок для jira_connect
    @patch('lit.PromptSession')
    @patch('builtins.print')
    @patch('lit.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_push_command(self, mock_file, mock_datetime, mock_print, mock_prompt_session, mock_jira_connect, mock_add_worklog): # mock_add_worklog
        # Настройка моков
        mock_datetime.side_effect = lambda *args, **kw: self.MockedDateTime(*args, **kw)
        mock_datetime.now.return_value = self.MockedDateTime.now()
        mock_datetime.strptime.side_effect = lambda *args: datetime.strptime(*args)
        mock_prompt_session.return_value.prompt.return_value = 'y'

        # Мокируем Jira подключение
        mock_jira = mock_jira_connect.return_value

        # Мокируем успешный вызов add_worklog
        mock_add_worklog.return_value = ('73546546', None)

        # Добавляем запись
        self.manager.add_entry(['TASK-123', '2', 'Тестовая запись'])
        self.assertEqual(len(self.manager.entries), 1)

        # Проверяем что запись сохранилась в файл
        expected_entry = "15.01.2023 [14:30 - 16:30] TASK-123 2h `Тестовая запись`\n"
        mock_file().write.assert_called_with(expected_entry)

        # Выполняем push
        self.manager.push_entries()

        # Проверяем, что .litstore сохранен с пустой строкой (после успешной отправки)
        mock_file.assert_any_call(LIT_STORE, 'w', encoding='utf-8')
        mock_file().write.assert_any_call("\n")

        # Проверяем, что .lithistory содержит успешную запись с ID
        mock_file.assert_any_call(LIT_HISTORY, 'a', encoding='utf-8')
        expected_history_entry = "15.01.2023 [14:30 - 16:30] TASK-123 2h `Тестовая запись` # 73546546\n"
        mock_file().write.assert_any_call(expected_history_entry)

        # Проверяет, что метод подключения к Jira был вызван ровно 1 раз.
        mock_jira_connect.assert_called_once()
        # Проверяет, что метод добавления ворклога вызывается с правильными параметрами
        mock_add_worklog.assert_called_once_with(
            mock_jira,
            'TASK-123',
            '2h',
            'Тестовая запись',
            '15.01.2023',
            '14:30'
        )

        # Проверяем вывод перед подтверждением
        mock_print.assert_any_call("\nПодготовленные записи:")
        mock_print.assert_any_call("\n15.01.2023")
        mock_print.assert_any_call("   [14:30 - 16:30] TASK-123 2h `Тестовая запись`")
        mock_print.assert_any_call("\nОтправка записей в Jira...")
        mock_print.assert_any_call("Записей успешно отправлено: 1")
        mock_print.assert_any_call("Записей неотправленных записей: 0")

    @patch('lit.PromptSession')
    @patch('builtins.print')
    @patch('lit.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_push_command_cancel(self, mock_file, mock_datetime, mock_print, mock_prompt_session):
        # Настройка моков
        mock_datetime.side_effect = lambda *args, **kw: self.MockedDateTime(*args, **kw)
        mock_datetime.now.return_value = self.MockedDateTime.now()
        mock_datetime.strptime.side_effect = lambda *args: datetime.strptime(*args)
        mock_prompt_session.return_value.prompt.return_value = 'N'

        # Добавляем запись
        self.manager.add_entry(['TASK-123', '2', 'Тестовая запись'])
        self.assertEqual(len(self.manager.entries), 1)

        # Проверяем что запись сохранилась в файл
        expected_entry = "15.01.2023 [14:30 - 16:30] TASK-123 2h `Тестовая запись`\n"
        mock_file().write.assert_called_with(expected_entry)

        # Выполняем push
        self.manager.push_entries()

        # Проверяем очистку записей
        self.assertEqual(len(self.manager.entries), 1)

        # Проверяем что запись сохранилась в файл
        expected_entry = "15.01.2023 [14:30 - 16:30] TASK-123 2h `Тестовая запись`\n"
        mock_file().write.assert_called_with(expected_entry)

        # Проверяем вывод перед подтверждением
        mock_print.assert_any_call("\nПодготовленные записи:")
        mock_print.assert_any_call("\n15.01.2023")
        mock_print.assert_any_call("   [14:30 - 16:30] TASK-123 2h `Тестовая запись`")
        mock_print.assert_any_call("Отмена отправки.")

    @patch('lit.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_cli_add_command(self, mock_file, mock_datetime):
        # Настройка фиктивного времени
        mock_datetime.side_effect = lambda *args, **kw: self.MockedDateTime(*args, **kw)
        mock_datetime.now.return_value = self.MockedDateTime.now()
        mock_datetime.strptime.side_effect = lambda *args: datetime.strptime(*args)

        # Симулируем передачу аргументов из CLI (как если бы они были получены через vars(args))
        cli_args = {
            'code': 'TASK-123',
            'hours': '40h',
            'message': 'Описание работы',
            'date': '15.01.2023',
            'time': '14:30'
        }

        # Выполняем команду CLI add
        self.manager.add_entry(cli_args)

        # Расчет времени окончания: 15.01.2023 14:30 + 50 часов = 17.01.2023 16:30
        expected_entry = "15.01.2023 [14:30 - 06:30] TASK-123 40h `Описание работы`\n"

        # Проверяем, что запись корректно записана в файл
        mock_file().write.assert_called_with(expected_entry)

class TestWorklogCompleter(unittest.TestCase):
    def setUp(self):
        self.completer = WorklogCompleter()
        # Имитируем данные для автодополнения
        global TASKS
        TASKS.clear()
        TASKS.update({
            "TASK-123": "Test Task 1",
            "PROJ-456": "Test Project Task"
        })

    def test_command_completion_basic(self):
        # Пустой ввод
        doc = Document(text="")
        completions = list(self.completer.get_completions(doc, None))
        self.assertEqual(
            {c.text for c in completions},
            {'add', 'status', 'push', 'pull', 'edit', 'init'}
        )

    def test_command_completion_partial(self):
        # Частичный ввод "p"
        doc = Document(text="p")
        completions = list(self.completer.get_completions(doc, None))
        self.assertEqual([c.text for c in completions], ['push', 'pull'])


class TestWorklogCompleterError(unittest.TestCase):
    def test_unclosed_single_quotation_mark(self):
        completer = WorklogCompleter()
        doc = Document(text="add TASK-123 0.5 '")
        try:
            list(completer.get_completions(doc, None))
        except Exception as e:
            self.fail(f"Autocompletion raised an exception: {e}")

    def test_unclosed_double_quotation_mark(self):
        completer = WorklogCompleter()
        doc = Document(text="add TASK-123 0.5 \"")
        try:
            list(completer.get_completions(doc, None))
        except Exception as e:
            self.fail(f"Autocompletion raised an exception: {e}")

    def test_unclosed_double_and_then_single_quotes_mark(self):
        completer = WorklogCompleter()
        doc = Document(text="add TASK-123 0.5 \"'")
        try:
            list(completer.get_completions(doc, None))
        except Exception as e:
            self.fail(f"Autocompletion raised an exception: {e}")

    def test_unclosed_single_and_then_double_quotes_mark(self):
        completer = WorklogCompleter()
        doc = Document(text="add TASK-123 0.5 '\"")
        try:
            list(completer.get_completions(doc, None))
        except Exception as e:
            self.fail(f"Autocompletion raised an exception: {e}")

    def test_unbalanced_quotes_autocompletion(self):
        completer = WorklogCompleter()
        doc = Document(text="add TASK-123 0.5 '\"'")
        try:
            list(completer.get_completions(doc, None))
        except Exception as e:
            self.fail(f"Autocompletion raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()