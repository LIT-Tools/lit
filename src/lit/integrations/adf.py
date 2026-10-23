"""Конверсия plain text -> Atlassian Document Format (ADF)."""
from __future__ import annotations

import re

# Управляющие символы C0, которые не являются допустимым текстом ADF.
# Табуляция (\x09) и переводы строк обрабатываются отдельно.
_INVALID_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def plain_text_to_adf(text: str) -> dict:
    """Обернуть plain text в минимальный ADF-документ.

    Каждая строка становится отдельным параграфом. Пустые и
    whitespace-only строки превращаются в пустой ``paragraph`` без
    текстового узла: ADF не принимает пустые ``text``-узлы.
    """
    if not text:
        return {"type": "doc", "version": 1, "content": []}

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    content = []
    for line in normalized.split("\n"):
        line = _INVALID_CONTROL.sub("", line)
        if line.strip():
            content.append(
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": line}],
                }
            )
        else:
            content.append({"type": "paragraph"})

    return {"type": "doc", "version": 1, "content": content}
