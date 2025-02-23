import unittest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timedelta
from lit import WorklogManager


class TestAddCommand(unittest.TestCase):
    @patch('lit.datetime')
    @patch('builtins.open', new_callable=mock_open)
    def test_add_command_success(self, mock_file, mock_datetime):
        # Настройка моков времени
        fixed_time = datetime(2023, 1, 15, 14, 30)

        class MockedDateTime(datetime):
            @classmethod
            def now(cls):
                return fixed_time

            def strftime(self, fmt):
                return fixed_time.strftime(fmt)

            def __add__(self, delta):
                return fixed_time + delta

        mock_datetime.side_effect = lambda *args, **kw: MockedDateTime(*args, **kw)
        mock_datetime.now.return_value = MockedDateTime.now()
        mock_datetime.strptime.side_effect = lambda *args: datetime.strptime(*args)

        # Выполнение команды
        manager = WorklogManager()
        args = ['-c', 'SOGAZ-123', '-l', '7', '-m', 'Описание работы']
        manager.add_entry(args)

        # Проверка формата записи
        entry = manager.entries[0]
        self.assertEqual(
            entry,
            "15.01.2023 [14:30 - 21:30] SOGAZ-123 7.0h `Описание работы`"
        )


if __name__ == '__main__':
    unittest.main()
