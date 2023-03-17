from json import load
from os import path
from collections import namedtuple

CONFIG = namedtuple(
    "CONFIG",
    ["TELEGRAM_BOT_TOKEN", "DATA_BOT_TEST_DIR", "SQLITE_DB_FILE", "MINIO_CREDENTIALS"],
)
_config_path = "data/config.json"
if not path.exists(_config_path):
    raise FileNotFoundError("Config not found!")
with open(_config_path, "r") as f:
    config = CONFIG(**load(f))
