#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import os
import string
from importlib import import_module
from pkgutil import iter_modules
import re
from urllib.parse import urlsplit
import json
import socket
from shutil import copy2, copystat


def walk_modules(path):
    """Loads a module and all its submodules from the given module path and
    returns them. If *any* module throws an exception while importing, that
    exception is thrown back.
    For example: walk_modules('devspace.utils')
    """

    mods = []
    mod = import_module(path)
    mods.append(mod)
    if hasattr(mod, '__path__'):
        for _, subpath, ispkg in iter_modules(mod.__path__):
            fullpath = path + '.' + subpath
            if ispkg:
                mods += walk_modules(fullpath)
            else:
                submod = import_module(fullpath)
                mods.append(submod)
    return mods


def url_validator(url: str):
    ul = '\u00a1-\uffff'  # Unicode letters range (must not be a raw string).

    # IP patterns
    ipv4_re = r'(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}'
    ipv6_re = r'\[[0-9a-f:.]+\]'  # (simple regex, validated later)

    # Host patterns
    hostname_re = r'[a-z' + ul + r'0-9](?:[a-z' + ul + r'0-9-]{0,61}[a-z' + ul + r'0-9])?'
    # Max length for domain name labels is 63 characters per RFC 1034 sec. 3.1
    domain_re = r'(?:\.(?!-)[a-z' + ul + r'0-9-]{1,63}(?<!-))*'
    tld_re = (
            r'\.'  # dot
            r'(?!-)'  # can't start with a dash
            r'(?:[a-z' + ul + '-]{2,63}'  # domain label
                              r'|xn--[a-z0-9]{1,59})'  # or punycode label
                              r'(?<!-)'  # can't end with a dash
                              r'\.?'  # may have a trailing dot
    )
    host_re = '(' + hostname_re + domain_re + tld_re + '|localhost)'
    regex = re.compile(
        r'^(?:[a-z0-9.+-]*)://'  # scheme is validated separately
        r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'  # user:pass authentication
        r'(?:' + ipv4_re + '|' + ipv6_re + '|' + host_re + ')'
        r'(?::\d{2,5})?'  # port
        r'(?:[/?#][^\s]*)?'  # resource path
        r'\Z', re.IGNORECASE)
    schemes = ['http', 'https']
    scheme = url.split('://')[0].lower()
    if scheme not in schemes:
        return False
    if len(urlsplit(url).netloc) > 253:
        return False
    return re.search(regex, url) is not None


def inside_project():
    return bool(find_project_config())


def find_project_config(path='.', prev_path=None):
    if path == prev_path:
        return ''
    path = os.path.abspath(path)
    conf_file = os.path.join(path, 'devspace.json')
    if os.path.exists(conf_file):
        return conf_file
    return find_project_config(os.path.dirname(path), path)


def get_project_settings(settings=None):
    conf_file = find_project_config()
    if settings and conf_file:
        with open(conf_file, 'r', encoding="utf-8") as f:
            values = f.read()
            settings.set_dict(values)


def get_project_dir():
    conf_file = find_project_config()
    return os.path.dirname(conf_file) if conf_file else ""


def arglist_to_dict(arglist):
    return dict(x.split('=', 1) for x in arglist)


def copytree(src, dst, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)

    for name in names:
        if name in ignored_names:
            continue

        src_name = os.path.join(src, name)
        dst_name = os.path.join(dst, name)
        if os.path.isdir(src_name):
            copytree(src_name, dst_name, ignore)
        else:
            copy2(src_name, dst_name)
    copystat(src, dst)


def render_template(template_path, dst_path, **kwargs):
    with open(template_path, 'rb') as fp:
        raw = fp.read().decode('utf8')

    content = string.Template(raw).safe_substitute(**kwargs)

    with open(dst_path, 'wb') as fp:
        fp.write(content.encode('utf8'))


def github_validator(name_or_repo: str):
    regex = re.compile(
        r'^([a-zA-Z\d](?:[a-zA-Z\d]|-(?=[a-zA-Z\d])){0,38})(\/[\w.-]{1,100})?$',
        re.IGNORECASE)
    return True if re.match(regex, name_or_repo) else False


def name_validator(name: str, length: int = 9):
    regex = re.compile(
        r'^([a-zA-Z\d](?:[a-zA-Z\d]|-(?=[a-zA-Z\d])){0,%s})$' % length,
        re.IGNORECASE)
    return True if re.match(regex, name) else False


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def get_path_uri(path):
    path = os.path.abspath(path)
    if sys.platform == "win32":
        scheme = "///"
        schema_path = path.replace('\\', '/')
    else:
        scheme = "//"
    return "file:{}{}/".format(scheme, schema_path)
