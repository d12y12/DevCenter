# -*- coding: UTF-8 -*-
from os.path import join, abspath, dirname

# Log
LOG_ENABLED = True
LOG_FORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
LOG_LEVEL = 'DEBUG'
LOG_STDOUT = False  # Default to stderr
LOG_FILE = None
LOG_ENCODING = 'utf-8'
LOG_MAX_BYTES = 1024 * 1024
LOG_BACKUP_COUNT = 3
LOG_PATH = "."

# Download
REQUESTS_CONNECTION_TIMEOUT = 15
REQUESTS_READ_TIMEOUT = 15
RETRY_ENABLED = False
RETRY_TIMES = 3
RETRY_INTERVAL = 3
RESULT_BACKUP = False
ENABLE_DEFAULT_SECTION = True
DEFAULT_SECTION_NAME = "Not classify"

COMMANDS_MODULE = ""

# Localization
LOCAL_TZ = "Asia/Shanghai"
LOCAL_DEBIAN_MIRROR = "http://mirrors.163.com"
LOCAL_PYTHON_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"

# Directories
TEMPLATES_DIR = abspath(join(dirname(__file__), '..', 'templates'))
APPS_DIR = abspath(join(dirname(__file__), '..', 'apps'))
SCHEMA_DIR = abspath(join(dirname(__file__), '..', 'schema'))

