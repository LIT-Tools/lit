import unittest
import io
import os
import contextlib
import argparse
from unittest.mock import patch, mock_open
from datetime import datetime
from lit import WorklogManager, WorklogCompleter, TASKS, COMMITS, LIT_STORE, LIT_HISTORY
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

        message = '''первая строка
        вторая строка'''

        self.manager.add_entry(['TASK-123', '7', 'Описание работы'])
        self.manager.add_entry(['TASK-123', '1,5', 'Описание работы'])
        self.manager.add_entry(['TASK-123', '0.5', 'Описание работы'])
        self.manager.add_entry(['TASK-123', '15m', 'Описание работы', '-d', '20.02.2024', '-t', '10:00'])
        self.manager.add_entry(['TASK-123', '1d', 'Описание работы', '-d', '20.02.2024', '-t', '10:00'])
        self.manager.add_entry(['TASK-123', '1', message, '-d', '21.02.2024', '-t', '10:00'])


        expected_content = (
            "15.01.2023 [14:30 - 21:30] TASK-123 7h `Описание работы`\n"
            "15.01.2023 [14:30 - 16:00] TASK-123 1,5h `Описание работы`\n"
            "15.01.2023 [14:30 - 15:00] TASK-123 0,5h `Описание работы`\n"
            "20.02.2024 [10:00 - 10:15] TASK-123 15m `Описание работы`\n"
            "20.02.2024 [10:00 - 18:00] TASK-123 1d `Описание работы`\n"
            "21.02.2024 [10:00 - 11:00] TASK-123 1h `первая строка\\n        вторая строка`\n"
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
        global TASKS, COMMITS
        TASKS.clear()
        TASKS.update({
            "TASK-123": "Implement feature X",
            "PROJ-456": "Fix critical bug",
            "DOC-789": "Update documentation",
        })

        COMMITS.clear()
        COMMITS.update( {
            "TASK-123": ["Add new API method", "Refactor module"],
            "PROJ-456": ["Emergency hotfix"],
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

    def test_add_command_empty_args(self):
        doc = Document(text="add ")
        completions = list(self.completer.get_completions(doc, None))
        expected = {f"{task} - {desc}"[:40] for task, desc in TASKS.items()}
        self.assertEqual({c.display[0][1] for c in completions}, expected)
        self.assertTrue(all(c.start_position == 0 for c in completions))

    def test_add_command_partial_task_code(self):
        doc = Document(text="add TAS")
        completions = list(self.completer.get_completions(doc, None))
        self.assertEqual(completions[0].text, "TASK-123")
        self.assertIn("Найдено в коде", completions[0].display_meta_text)

    def test_add_command_time_suggestions(self):
        doc = Document(text="add TASK-123 ")
        completions = list(self.completer.get_completions(doc, None))
        expected = ["1", "30m", "2h", "1d", "4h", "3h", "'1h 30m'", "15m", "20m", "10m"]
        self.assertEqual([c.text for c in completions], expected)

    def test_add_command_message_suggestions(self):
        doc = Document(text="add TASK-123 2h ")
        completions = list(self.completer.get_completions(doc, None))
        expected = ["'Add new API method'", "'Refactor module'"]
        self.assertEqual([f"'{c.display[0][1]}'" for c in completions], expected)

    def test_add_command_param_suggestions(self):
        doc = Document(text="add TASK-123 2h message -")
        completions = list(self.completer.get_completions(doc, None))
        self.assertEqual(
            {c.text for c in completions},
            {'-d', '-t'}
        )

    def test_pull_command_param_suggestions(self):
        doc = Document(text="pull ")
        completions = list(self.completer.get_completions(doc, None))
        self.assertEqual(
            {c.text for c in completions},
            {'--jira', '--gitlab'}
        )

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


class TestVersionCommand(unittest.TestCase):

    @patch('lit.get_version', return_value="1.2.3")
    def test_cli_version(self, mock_get_version):
        """
        Проверка работы версии в CLI‑режиме.
        Создаём локальный парсер с параметром --version и проверяем,
        что при его передаче выводится корректная версия и происходит завершение работы.
        """

        from lit import get_version

        parser = argparse.ArgumentParser(description="Утилита для работы с ворклогами.")
        parser.add_argument(
            '-v', '--version',
            action='version',
            version=f"lit v{get_version()}",
            help="Показать версию и выйти"
        )
        a = get_version()
        # Перехватываем вывод
        with patch('sys.stdout', new_callable=io.StringIO) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                parser.parse_args(['--version'])
            self.assertEqual(cm.exception.code, 0)
            # Проверяем, что версия выведена корректно
            expected_output = "lit v1.2.3\n"
            self.assertEqual(fake_out.getvalue(), expected_output)


class TestInteractiveVersion(unittest.TestCase):
    @patch('lit.patch_stdout', new=lambda: contextlib.nullcontext())
    @patch('lit.PromptSession')
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('lit.get_version', return_value="1.2.3")
    def test_interactive_version(self, mock_get_version, mock_stdout, mock_prompt_session):
        """
        Эмулируем ввод в интерактивном режиме: первым вводом передаём '--version',
        после чего выбрасываем KeyboardInterrupt для завершения основного цикла.
        Проверяем, что в выводе присутствует строка с версией.
        """
        # Эмулируем ввод '--version' и затем остановку цикла.
        instance = mock_prompt_session.return_value
        instance.prompt.side_effect = ['--version', KeyboardInterrupt()]

        from lit import main, create_argument_parser

        try:
            parser = create_argument_parser()
            main(parser)
        except KeyboardInterrupt:
            pass

        output = mock_stdout.getvalue()
        self.assertIn("lit v1.2.3", output)


class TestHelpCommand(unittest.TestCase):

    def test_cli_help(self):
        """
        Проверка работы параметра --help в CLI-режиме.
        Используем стандартный парсер с автоматически добавленным --help
        и проверяем, что при его передаче выводится справка
        """
        parser = argparse.ArgumentParser(description="Утилита для работы с ворклогами.")
        # Добавим другой тестовый аргумент (--help создается автоматически)
        parser.add_argument('-v', '--version', help="Показать версию")

        # Перехватываем вывод
        with patch('sys.stdout', new_callable=io.StringIO) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                parser.parse_args(['--help'])
            self.assertEqual(cm.exception.code, 0)

            # Проверяем, что справка содержит ключевые фразы
            help_output = fake_out.getvalue()
            self.assertIn("Утилита для работы с ворклогами", help_output)
            self.assertIn("--help", help_output)
            self.assertIn("--version", help_output)


class TestInteractiveHelp(unittest.TestCase):
    @patch('lit.patch_stdout', new=lambda: contextlib.nullcontext())
    @patch('lit.PromptSession')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_interactive_help(self, mock_stdout, mock_prompt_session):
        """
        Эмулируем ввод в интерактивном режиме: первым вводом передаём '--help',
        после чего выбрасываем KeyboardInterrupt для завершения основного цикла.
        Проверяем, что в выводе содержится текст справки.
        """
        # Эмулируем ввод '--help' и затем остановку цикла.
        instance = mock_prompt_session.return_value
        instance.prompt.side_effect = ['--help', KeyboardInterrupt()]

        from lit import main, create_argument_parser

        try:
            parser = create_argument_parser()
            main(parser)
        except KeyboardInterrupt:
            pass

        # Проверяем, что вывод содержит характерные для справки фразы
        output = mock_stdout.getvalue()
        self.assertIn("usage:", output.lower())  # Проверяем, что содержится характерное для справки слово "usage:"
        # Можно добавить дополнительные проверки на содержимое справки
        self.assertIn("--help", output)


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.manager = WorklogManager()
        self.manager.entries = []
        self.mock_print = patch('builtins.print').start()
        self.file_mock = patch('builtins.open', mock_open()).start()

        # Мокируем глобальные переменные
        global TASKS, COMMITS
        TASKS.clear()
        TASKS.update({
            'VALID-123': 'Valid Task',
            'VALID-456': 'Another Task'
        })

    def tearDown(self):
        patch.stopall()

    def _call_add_entry(self, code, hours, message, date='01.01.2023', time='10:00'):
        args = {
            'code': code,
            'hours': hours,
            'message': message,
            'date': date,
            'time': time
        }
        return self.manager.add_entry(args)

    # Тесты формата кода задачи
    def test_valid_task_code(self):
        try:
            self._call_add_entry('VALID-123', '2h', 'Valid task')
        except ValueError:
            self.fail("Valid code raised unexpected ValueError")

    def test_invalid_task_code_format(self):
        invalid_codes = [
            'VAL-12a',  # letter in number
            'V-123',  # too short prefix
            'VALID123'  # missing dash
        ]

        for code in invalid_codes:
            with self.subTest(code=code):
                self._call_add_entry(code, '2h', 'Message')
                self.mock_print.assert_any_call(
                    f"⛔ Ошибка: Неверный формат кода задачи: {code.upper()}. Ожидается формат: ABC-123"
                )

    # Тесты существования задачи в системе
    def test_existing_task_no_warning(self):
        self._call_add_entry('VALID-123', '2h', 'Message')
        self.mock_print.assert_not_called()

    def test_non_existing_task_warning(self):
        self._call_add_entry('NONEX-999', '3h', 'Message')
        self.mock_print.assert_called_with(
            "⚠️ Внимание: Задача NONEX-999 не найдена в системе. Запись будет создана с ручным вводом!"
        )

    # Тесты времени начала
    def test_late_start_time_warning(self):
        self._call_add_entry('VALID-123', '1h', 'Late work', time='20:00')
        self.mock_print.assert_any_call(
            "⚠️ Внимание: В задаче VALID-123 указано время начала 20:00 для даты 01.01.2023!"
        )

    def test_early_start_time_warning(self):
        self._call_add_entry('VALID-123', '30m', 'Early work', time='04:30')
        self.mock_print.assert_any_call(
            "⚠️ Внимание: В задаче VALID-123 указано время начала 04:30 для даты 01.01.2023!"
        )

    def test_invalid_hours_format(self):
        invalid_formats = ['abc', '12x', 'h2', '1.5hrs', 'm30']

        for fmt in invalid_formats:
            with self.subTest(format=fmt):
                self._call_add_entry('VALID-123', fmt, 'Test')
                self.mock_print.assert_any_call(
                    f"⛔ Ошибка: Неверный формат количества времени. Ожидается, например, '1h 15m' или '8'."
                )


class TestPullEntries(unittest.TestCase):
    def setUp(self):
        self.manager = WorklogManager()

    @patch('lit.load_tasks_from_jira')
    @patch('lit.load_commits_from_gitlab')
    def test_cli_mode(self, mock_gitlab, mock_jira):
        """Тестируем вызов из CLI с явными параметрами"""
        test_cases = [
            # kwargs, should_call_jira, should_call_gitlab
            ({'jira': True, 'gitlab': False}, True, False),
            ({'jira': False, 'gitlab': True}, False, True),
            ({'jira': True, 'gitlab': True}, True, True),
            ({'jira': False, 'gitlab': False}, True, True)  # По умолчанию вызываются оба
        ]

        for kwargs, should_call_jira, should_call_gitlab in test_cases:
            with self.subTest(**kwargs):
                # Вызываем тестируемую функцию
                self.manager.pull_entries(jira=kwargs['jira'], gitlab=kwargs['gitlab'])

                # Проверяем вызовы согласно ожидаемым значениям
                if should_call_jira:
                    mock_jira.assert_called_once()
                else:
                    mock_jira.assert_not_called()

                if should_call_gitlab:
                    mock_gitlab.assert_called_once()
                else:
                    mock_gitlab.assert_not_called()

                # Сбрасываем моки для следующего теста
                mock_jira.reset_mock()
                mock_gitlab.reset_mock()

    @patch('lit.load_tasks_from_jira')
    @patch('lit.load_commits_from_gitlab')
    def test_interactive_mode(self, mock_gitlab, mock_jira):
        """Тестируем интерактивный режим с разными аргументами"""
        test_cases = [
            (['--jira'], True, False),
            (['--gitlab'], False, True),
            ([], True, True),
        ]

        for args, jira_expected, gitlab_expected in test_cases:
            with self.subTest(args=args):
                self.manager.pull_entries(args=args)

                if jira_expected:
                    mock_jira.assert_called_once()
                else:
                    mock_jira.assert_not_called()

                if gitlab_expected:
                    mock_gitlab.assert_called_once()
                else:
                    mock_gitlab.assert_not_called()

                mock_jira.reset_mock()
                mock_gitlab.reset_mock()

        # Отдельный тест для неверного аргумента
        # with self.subTest(args=['invalid_arg']):
        #     with self.assertRaises(argparse.ArgumentError):
        #         self.manager.pull_entries(args=['invalid_arg'])

    @patch('lit.argparse.ArgumentParser.parse_args')
    @patch('lit.load_tasks_from_jira')
    def test_parser_error_handling(self, mock_jira, mock_parse):
        """Тестируем обработку ошибок парсера"""
        mock_parse.side_effect = SystemExit()
        self.manager.pull_entries(args=['--invalid-arg'])
        mock_jira.assert_not_called()


class TestEditEntries(unittest.TestCase):
    def setUp(self):
        self.manager = WorklogManager()
        self.mock_print = patch('builtins.print').start()
        self.mock_subprocess = patch('subprocess.run').start()
        self.mock_load = patch.object(WorklogManager, '_load').start()

        # Мокируем глобальные переменные
        self.patcher = patch.multiple('lit',
                                      LIT_STORE='/fake/path/.litstore',
                                      CUSTOM_EDITOR=''
                                      )
        self.patcher.start()

    def tearDown(self):
        patch.stopall()
        self.patcher.stop()

    @patch.dict(os.environ, {}, clear=True)
    @patch('os.name', 'nt')
    def test_windows_default_editor(self):
        self.manager.edit_entries()
        self.mock_subprocess.assert_called_once_with(
            ['notepad', '/fake/path/.litstore'],
            shell=True,
            check=True,
            encoding='utf-8'
        )
        self.mock_load.assert_called_once()
        self.mock_print.assert_any_call(['notepad', '/fake/path/.litstore'])
        self.mock_print.assert_any_call("✓ Изменения применены")

    @patch.dict(os.environ, {'EDITOR': 'nano'}, clear=True)
    @patch('os.name', 'posix')
    def test_unix_editor_from_env(self):
        self.manager.edit_entries()
        self.mock_subprocess.assert_called_once_with(
            ['nano', '/fake/path/.litstore'],
            shell=False,
            check=True,
            encoding='utf-8'
        )

if __name__ == '__main__':
    unittest.main()