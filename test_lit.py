import unittest
import os
from unittest.mock import patch, mock_open
from datetime import datetime
from lit import WorklogManager, LOG_FILE


class TestWorklogManager(unittest.TestCase):
    def setUp(self):
        self.manager = WorklogManager()
        self.manager.entries = []

    def tearDown(self):
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)

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
    def test_add_command_success(self, mock_file, mock_datetime):
        mock_datetime.side_effect = lambda *args, **kw: self.MockedDateTime(*args, **kw)
        mock_datetime.now.return_value = self.MockedDateTime.now()
        mock_datetime.strptime.side_effect = lambda *args: datetime.strptime(*args)

        args = ['-c', 'SOGAZ-123', '-l', '7', '-m', 'Описание работы']
        self.manager.add_entry(args)

        expected_entry = "15.01.2023 [14:30 - 21:30] SOGAZ-123 7.0h `Описание работы`\n"
        mock_file().write.assert_called_once_with(expected_entry)

    @patch('lit.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_full_add_command_success(self, mock_file, mock_datetime):
        mock_datetime.side_effect = lambda *args, **kw: self.MockedDateTime(*args, **kw)
        mock_datetime.now.return_value = self.MockedDateTime.now()
        mock_datetime.strptime.side_effect = lambda *args: datetime.strptime(*args)

        args = ['-c', 'SOGAZ-123', '-l', '7', '-m', 'Описание работы', '-d', '20.02.2024', '-t', '10:00']
        self.manager.add_entry(args)

        expected_entry = "20.02.2024 [10:00 - 17:00] SOGAZ-123 7.0h `Описание работы`\n"
        mock_file().write.assert_called_once_with(expected_entry)

    @patch('lit.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_two_entries_success(self, mock_file, mock_datetime):
        mock_datetime.side_effect = lambda *args, **kw: self.MockedDateTime(*args, **kw)
        mock_datetime.now.return_value = self.MockedDateTime.now()
        mock_datetime.strptime.side_effect = lambda *args: datetime.strptime(*args)

        self.manager.add_entry(['-c', 'SOGAZ-123', '-l', '2', '-m', 'Первая запись'])
        self.manager.add_entry(['-c', 'SOGAZ-44', '-l', '1.5', '-m', 'Вторая запись'])

        expected_content = (
            "15.01.2023 [14:30 - 16:30] SOGAZ-123 2.0h `Первая запись`\n"
            "15.01.2023 [14:30 - 16:00] SOGAZ-44 1.5h `Вторая запись`\n"
        )
        mock_file().write.assert_called_with(expected_content)


if __name__ == '__main__':
    unittest.main()