import os
from pathlib import Path

LIT_DIR = str(Path("~/.lit").expanduser())
LIT_STORE = os.path.join(LIT_DIR, ".litstore")
LIT_HISTORY = os.path.join(LIT_DIR, ".lithistory")
CONFIG_FILE = os.path.join(LIT_DIR, ".litconfig")
COMMITS_FILE = os.path.join(LIT_DIR, "commits.json")
TASKS_FILE = os.path.join(LIT_DIR, "tasks.json")

os.makedirs(LIT_DIR, exist_ok=True)
