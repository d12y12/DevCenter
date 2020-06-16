#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import string
import os
import json
from os.path import join, isdir
from shutil import ignore_patterns
from devspace.utils.misc import render_template, copytree
from devspace.servers import DevSpaceServer
import subprocess
import yaml


TEMPLATES_MAPPING = {
    # ${maintainer}, ${localization}, ${image}, ${port}
    "Dockerfile": ("${TEMPLATES_DIR}/DocBuilder/Dockerfile-${image}.template",
                   "${project_dir}/servers/DocBuilder/Dockerfile"),
    # ${server_name}
    'DockerCompose': ('${TEMPLATES_DIR}/DocBuilder/server.yaml.template', ''),
}


class DocBuilder(DevSpaceServer):
    type = 'DocBuilder'
    image_support = ['debian', 'alpine']

    def __init__(self, server_settings=None):
        self.builder = []
        super().__init__(server_settings)
        self.templates_mapping = json.loads(string.Template(json.dumps(TEMPLATES_MAPPING)).safe_substitute(
            TEMPLATES_DIR=self.settings.get("TEMPLATES_DIR", "").replace("\\", "/"),
            image=self.image,
            project_dir=self.settings['project']['path'].replace("\\", "/")
        ))

    def load_settings(self):
        super().load_settings()
        if self.settings['services']:
            for service_name, service_setting in self.settings['services'].items():
                if self.__class__.__name__ in service_setting:
                    self.services[service_name] = service_setting[self.__class__.__name__]
                    if 'builder' in service_setting[self.__class__.__name__].keys():
                        self.builder.append(service_setting[self.__class__.__name__]['builder'])

    def dockerfile(self, tz=True, distros=True, python=True):
        # ${docbook_builder} ${sphnix_builder}
        super().dockerfile(tz, distros, python)
        dst_file = self.templates_mapping['Dockerfile'][1]

        docbook_builder = ""
        sphnix_builder = ""
        builder = []
        for service_name, service in self.services.items():
            builder.append(service['builder'])
        if "docbook" in builder:
            if self.image == 'alpine':
                docbook_builder = "libxslt \\"
            else:
                docbook_builder = "xsltproc \\"
        if "sphnix" in builder:
            sphnix_builder = "&& pip3 install --no-cache-dir sphinx sphinx_rtd_theme recommonmark \\"
        render_template(dst_file, dst_file, docbook_builder=docbook_builder,
                        sphnix_builder=sphnix_builder)

    def create_server_structure(self):
        self.create_server_base_structure(ignore_patterns('*.template'))
        # make www
        www_dir = self.settings.get("SHARED_WEB", "")
        os.makedirs(www_dir, exist_ok=True)
        # make data dir
        data_dir = self.settings.get("SHARED_DATA", "")
        os.makedirs(data_dir, exist_ok=True)
        for service_name, service in self.services.items():
            service_dir = join(data_dir, service_name)
            os.makedirs(service_dir, exist_ok=True)
            os.makedirs(join(www_dir, 'services', service_name), exist_ok=True)
            if len(os.listdir(service_dir)) == 0 and service['source']:
                if isdir(service['source']):
                    copytree(service['source'], service_dir)
                else:
                    ret = subprocess.run(["git", "clone",  service['source'], service_dir], stdout=subprocess.DEVNULL)
                    if ret.returncode != 0:
                        raise RuntimeError("can't clone {}".format(service['source']))
            else:
                pass

    def render(self):
        self.create_server_structure()
        self.dockerfile()

    def generate_docker_compose_service(self):
        template_file = self.templates_mapping['DockerCompose'][0]
        with open(template_file, 'rb') as fp:
            raw = fp.read().decode('utf8')
            content = string.Template(raw).safe_substitute(
                server_name=(self.settings['project']['name'] + '_' + self.server_name).lower())
        service_content = yaml.safe_load(content)
        service_content['docbuilder']['volumes']=[]
        for service_name, service in self.services.items():
            service_content['docbuilder']['volumes'].append('./data/{}:/docs/{}'.format(service_name, service_name))
            service_content['docbuilder']['volumes'].append(
                './www/services/{}:/output/{}'.format(service_name, service_name))
        content = yaml.safe_dump(service_content)
        return content if content else ''
