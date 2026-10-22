import json
import shlex
from datetime import datetime


def sort_key(item):
    # Приоритет disabled: сначала None, потом остальные
    disabled_priority = 0 if item.get('disabled') is None else 1

    # Преобразование даты в объект для сравнения
    date_str = item.get('date', '31.12.9999')  # Для элементов без даты
    try:
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
    except:
        date = datetime.max.date()

    # Преобразование времени начала
    start_str = item.get('start', '23:59')  # Для элементов без времени
    try:
        start = datetime.strptime(start_str, '%H:%M').time()
    except:
        start = datetime.max.time()

    return (disabled_priority, date, start)


def load_dict(path_file) -> dict:
    """Загрузка коммитов из файла"""
    try:
        with open(path_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Если файла нет - создаём с начальными данными
        return {}
    except json.JSONDecodeError:
        # Битый файл
        print(f"ERROR: Invalid JSON format.")
        return {}


def safe_split(text):
    """
    Разбирает строку с учётом кавычек.
    Если остаётся незакрытая кавычка, она дописывается в конец строки.
    Экранирование не учитывается.
    """
    open_quote = None
    for ch in text:
        if ch in ("'", '"'):
            if open_quote is None:
                open_quote = ch  # начинаем секцию
            elif open_quote == ch:
                open_quote = None  # закрываем секцию
            # Если текущая кавычка не соответствует открытой,
            # она считается обычным символом внутри кавычек.
    if open_quote is not None:
        text += open_quote  # дописываем закрывающую кавычку
    return shlex.split(text)