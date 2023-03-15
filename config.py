from json import load
from os import path
from collections import namedtuple

CONFIG = namedtuple(
    "CONFIG", [
        "TELEGRAM_BOT_TOKEN",
        "DATA_BOT_TEST_DIR",
        "SQLITE_DB_FILE",
        "MINIO_CREDENTIALS"
    ]
)
_config_path = "data/config.json"
if not path.exists(_config_path):
    raise ValueError("Config not found!")
with open ("data/config.json", 'r') as f:
    config = CONFIG(**load(f))