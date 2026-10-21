import sys
from integrations import jira_push as _m
sys.modules[__name__] = _m
