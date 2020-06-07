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

COMMANDS_MODULE = ""

# Localization
LOCAL_TZ = "Asia/Shanghai"
LOCAL_DEBIAN_MIRROR = "http://mirrors.163.com"
LOCAL_ALPINE_MIRROR = "http://mirrors.ustc.edu.cn"
LOCAL_UBUNTU_MIRROR = "http://mirrors.ustc.edu.cn"
LOCAL_PYTHON_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"

# IMAGES
IMAGE_ALPINE = "alpine:3.12"
IMAGE_DEBIAN = "debian:buster-slim"
IMAGE_UBUNTU = ""

# Directories
TEMPLATES_DIR = abspath(join(dirname(__file__), '..', 'templates'))
SCHEMA_DIR = abspath(join(dirname(__file__), '..', 'schema'))
