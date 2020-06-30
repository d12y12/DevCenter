#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import string
import os
import yaml
from os.path import join, normpath, isfile, exists
import json
from shutil import ignore_patterns, copy2
from devspace.utils.misc import render_template, copytree
from devspace.servers import DevSpaceServer
import subprocess

TEMPLATES_MAPPING = {
    # ${maintainer}, ${localization}, ${image}, ${port}
    "Dockerfile": ("${TEMPLATES_DIR}/GitMirror/Dockerfile-${image}${cron}.template",
                   "${project_dir}/servers/GitMirror/Dockerfile"),
    # ${nginx_service} ${port}
    "Sqlite": ("${TEMPLATES_DIR}/GitMirror/apps/database/repository.sql.template",
               "${project_dir}/servers/GitMirror/apps/database/${service_name}.sql"),
    # ${server_name}
    'DockerCompose': ('${TEMPLATES_DIR}/GitMirror/server.yaml.template', ''),
}

APP_SRC = 'https://github.com/d12y12/GitMirror.git'


class GitMirror(DevSpaceServer):
    type = 'GitMirror'
    image_support = ['debian', 'alpine']
    support_repository_type = ['cgit', 'github']

    def __init__(self, server_settings=None):
        self.cron = False
        super().__init__(server_settings)
        self.templates_mapping = json.loads(string.Template(json.dumps(TEMPLATES_MAPPING)).safe_substitute(
            TEMPLATES_DIR=self.settings.get("TEMPLATES_DIR", "").replace("\\", "/"),
            image=self.image,
            project_dir=self.settings['project']['path'].replace("\\", "/"),
            cron="" if not self.cron else "-cron"
        ))

    def load_settings(self):
        super().load_settings()
        if self.settings['services']:
            for service_name, service_setting in self.settings['services'].items():
                if self.__class__.__name__ in service_setting:
                    self.services[service_name] = service_setting[self.__class__.__name__]
                    if 'synchronization' in service_setting[self.__class__.__name__].keys():
                        self.cron = True

    def sqlite(self):
        # ${title}, ${description}, ${max-repo-count},${service_name}
        server_settings = self.settings['servers']
        host = "localhost"
        port = "8080"
        if 'Web' in server_settings and 'host' in server_settings['Web']:
            host = server_settings['Web']['host']
        if 'Web' in server_settings and 'port' in server_settings['Web']:
            port = server_settings['Web']['port']
        host = '{}:{}'.format(host, port)
        for service_name, service in self.services.items():
            consistency = 0
            crontab = ""
            if 'synchronization' in service.keys():
                if 'consistency' in service['synchronization']:
                    consistency = 1 if service['synchronization']['consistency'] else 0
                if 'crontab' in service['synchronization']:
                    crontab = service['synchronization']['crontab']
                del service['synchronization']
            repositories = json.dumps(service)
            template_file = self.templates_mapping['Sqlite'][0]
            dst_file = self.templates_mapping['Sqlite'][1]
            dst_file = string.Template(dst_file).safe_substitute(service_name=service_name)
            render_template(template_file, dst_file, consistency=consistency, crontab=crontab,
                            repositories=repositories, service_name=service_name, host=host)

    def create_server_structure(self):
        self.create_server_base_structure(ignore_patterns('*.template', 'apps'))
        prj_srv_dir = join(self.settings['project']['path'], "servers", self.server_name)
        # generate apps
        apps_dir = join(prj_srv_dir, 'apps')
        os.makedirs(apps_dir, exist_ok=True)
        if not exists(join(apps_dir, '.git')):
            ret = subprocess.run(["git", "clone", APP_SRC, apps_dir], stdout=subprocess.DEVNULL)
            if ret.returncode != 0:
                raise RuntimeError("Clone app failed, please try render again")
        else:
            pass
        # make data dir
        data_dir = self.settings.get("SHARED_DATA", "")
        os.makedirs(data_dir, exist_ok=True)
        for service_name, service in self.services.items():
            os.makedirs(join(data_dir, service_name), exist_ok=True)
        # make log root
        log_dir = join(self.settings.get("SHARED_LOG", ""), self.server_name)
        os.makedirs(log_dir, exist_ok=True)

    def render(self):
        self.create_server_structure()
        self.dockerfile()
        self.sqlite()

    def generate_docker_compose_service(self):
        template_file = self.templates_mapping['DockerCompose'][0]
        with open(template_file, 'rb') as fp:
            raw = fp.read().decode('utf8')
            content = string.Template(raw).safe_substitute(
                server_name=(self.settings['project']['name'] + '_' + self.server_name).lower())
        service_content = yaml.safe_load(content)
        for service_name, service in self.services.items():
            service_content['gitmirror']['volumes'].append('./data/{}:/srv/git/{}'.format(service_name, service_name))
        content = yaml.safe_dump(service_content)
        return content if content else ''
