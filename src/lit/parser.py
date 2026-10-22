import re


def pars_store(file):
    pattern = re.compile(r'''
    ^
        (?:(?P<disabled>\#)\s?)?                                 # Признак, что строка отключена
        (?P<date>\d{2}\.\d{2}\.\d{4})\s+                         # Дата
        \[(?P<start>\d{2}:\d{2})\s*-\s*(?P<end>\d{2}:\d{2})]\s+  # Время
        (?P<code>\S+)\s+                                         # Код задачи
        (?P<duration>\d+[.,]?\d*[dhm]\s*(?:\d+[.,]?\d*m)?)\s+    # Длительность
        `(?P<message>.*?)`\s?                                    # Сообщение
        (?:\#\s?(?P<error>.*))?                                  # Ошибка (опционально)
    $
    ''', re.IGNORECASE | re.VERBOSE)

    logs = []
    for line in file:
        match = pattern.match(line)
        if match:
            logs.append(match.groupdict() | {"log": line})
        else:
            logs.append({'disabled': 'X', 'log': line})

    return logs
