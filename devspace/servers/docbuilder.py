#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import string
import os
import yaml
from os.path import join
import json
from shutil import ignore_patterns
from devspace.utils.misc import render_template
from devspace.servers import DevSpaceServer


TEMPLATES_MAPPING = {
    # ${maintainer}, ${localization}, ${image}, ${port}
    "Dockerfile": ("${TEMPLATES_DIR}/DocBuilder/Dockerfile-${image}${cron}.template",
                   "${project_dir}/servers/DocBuilder/Dockerfile"),
    # ${server_name}
    'DockerCompose': ('${TEMPLATES_DIR}/DocBuilder/server.yaml.template', ''),
    # ${volume} ${container_name} ${shell}
    'StartScript': ("${TEMPLATES_DIR}/DocBuilder/scripts/start.template",
                    "${project_dir}/servers/DocBuilder/scripts/start.${ext}")
}

APP_SRC = 'https://github.com/d12y12/DocBuilder.git'


class DocBuilder(DevSpaceServer):
    type = 'DocBuilder'
    image_support = ['debian', 'alpine']
    support_builder_type = ['docbook', 'sphinx']

    def __init__(self, server_settings=None):
        self.cron = False
        self.builder = []
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
                    self.services[service_name]['needWeb'] = False
                    if 'builder' in service_setting[self.__class__.__name__].keys():
                        self.builder.append(service_setting[self.__class__.__name__]['builder'])
                    if 'Web' in service_setting:
                        self.services[service_name]['needWeb'] = True
                    if 'synchronization' in service_setting[self.__class__.__name__].keys():
                        self.cron = True

    def dockerfile(self, tz=True, distros=True, python=True):
        # ${docbook_builder} ${sphnix_builder}
        super().dockerfile(tz, distros, python)
        dst_file = self.templates_mapping['Dockerfile'][1]

        docbook_builder = ""
        sphnix_builder = ""

        if "docbook" in self.builder:
            if self.image == 'alpine':
                docbook_builder = "libxslt \\"
            else:
                docbook_builder = "xsltproc \\"
        if "sphinx" in self.builder:
            sphnix_builder = "&& pip3 install --no-cache-dir sphinx sphinx_rtd_theme recommonmark \\"
        render_template(dst_file, dst_file, docbook_builder=docbook_builder,
                        sphnix_builder=sphnix_builder)

    def start_script_service_volume(self):
        volume = ''
        for service_name, service in self.services.items():
            volume += '\n' + ' ' * 11 + '-v {}/data/{}:/docs/{} \\'.format(self.settings['project']['path'],
                                                                           service_name, service_name)
            if service['needWeb']:
                volume += '\n' + ' ' * 11 + '-v {}/www/services/{}:/share/{} \\'.format(
                    self.settings['project']['path'],
                    service_name, service_name)
        return volume

    def create_server_structure(self):
        self.create_server_base_structure(ignore_patterns('*.template'))
        self.install_app(APP_SRC)
        prj_srv_dir = join(self.settings['project']['path'], "servers", self.server_name)
        # generate database
        database = join(prj_srv_dir, 'apps', 'database.json')
        with open(database, 'w', encoding="utf-8") as f:
            json.dump(self.services, f, indent=2, ensure_ascii=False)
        # make www
        www_dir = self.settings.get("SHARED_WEB", "")
        os.makedirs(www_dir, exist_ok=True)
        # make data dir
        data_dir = self.settings.get("SHARED_DATA", "")
        os.makedirs(data_dir, exist_ok=True)
        for service_name, service in self.services.items():
            os.makedirs(join(data_dir, service_name), exist_ok=True)
            if service['needWeb']:
                os.makedirs(join(www_dir, 'services', service_name), exist_ok=True)
        # make log root
        log_dir = join(self.settings.get("SHARED_LOG", ""), self.server_name)
        os.makedirs(log_dir, exist_ok=True)

    def render(self):
        self.create_server_structure()
        self.dockerfile()
        if not self.cron:
            self.start_script()

    def generate_docker_compose_service(self):
        template_file = self.templates_mapping['DockerCompose'][0]
        with open(template_file, 'rb') as fp:
            raw = fp.read().decode('utf8')
            content = string.Template(raw).safe_substitute(
                server_name=(self.settings['project']['name'] + '_' + self.server_name).lower())
        service_content = yaml.safe_load(content)
        for service_name, service in self.services.items():
            service_content['docbuilder']['volumes'].append('./data/{}:/docs/{}'.format(service_name, service_name))
            if service['needWeb']:
                service_content['docbuilder']['volumes'].append('./www/services/{}:/share/{}'.format(service_name,
                                                                                                     service_name))
        content = yaml.safe_dump(service_content)
        return content if content else ''
