# Deprecated shim: см. integrations/gitlab
# sys.modules-подмена (а не `from X import *`) нужна, чтобы
# patch("<old_module>.<attr>") и patch("integrations.<module>.<attr>")
# указывали на одно место. Удалить после перевода тестов на новый
# namespace (Шаг 4.5 / финальный src/-переезд).
import sys
from integrations import gitlab as _m
sys.modules[__name__] = _m
