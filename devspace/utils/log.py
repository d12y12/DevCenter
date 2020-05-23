#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import logging
from logging.handlers import RotatingFileHandler
from devspace import settings


class Log(object):
    def __init__(self, name, settings=None):
        if settings is None:
            self.settings = settings()
        else:
            self.settings = settings
        name = name.lower()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(settings['LOG_LEVEL'])
        self.formatter = logging.Formatter(settings['LOG_FORMAT'])
        self.log_file = RotatingFileHandler(os.path.join(settings['LOG_PATH'], name+'.log'),
                                            maxBytes=settings['LOG_MAX_BYTES'],
                                            backupCount=settings['LOG_BACKUP_COUNT'])
        self.log_file.setFormatter(self.formatter)
        self.console = logging.StreamHandler()
        self.console.setFormatter(self.formatter)
        if settings.get_bool('LOG_ENABLED'):
            self.logger.addHandler(self.log_file)
            self.logger.addHandler(self.console)
        else:
            self.logger.addHandler(logging.NullHandler())

    def getLogger(self):
        return self.logger
