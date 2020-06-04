#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, path)


from devspace.cmdline import execute

if __name__ == '__main__':
    execute()
