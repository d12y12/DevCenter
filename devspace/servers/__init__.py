#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import yaml
import string
from os.path import join, normpath
from jsonschema import validate, RefResolver
from devspace.settings import Settings
from devspace.exceptions import ConfigurationError
from devspace.utils.misc import get_path_uri, get_project_dir, get_project_host, get_project_author


class PrettyDumper(yaml.SafeDumper):
    yaml.SafeDumper.add_representer(
        type(None),
        lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:null', '')
    )

    def increase_indent(self, flow=False, indentless=False):
        return super(PrettyDumper, self).increase_indent(flow, False)


class DevSpaceServer:

    type = ''
    image_support = ['debian', 'alpine', 'ubuntu']

    def __init__(self, server_settings=None):
        self.server_name = ''
        self.image = ''
        self.port = -1
        self.services = []
        self.settings = Settings()
        self.localization = False
        self.host = get_project_host()
        self.author = get_project_author()
        self.settings.set('project_dir', get_project_dir())
        if server_settings:
            self.load_settings(server_settings)

    def valid_settings(self, server_settings):
        try:
            if isinstance(server_settings, str):
                server_settings = json.loads(server_settings)
            server_name = list(server_settings.keys())[0]
            server_settings = server_settings[server_name]
            schema_dir = self.settings.get('SCHEMA_DIR', '')
            schema_name = self.type.lower() + '_schema.json'
            schema_file = os.path.join(schema_dir, schema_name)
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            resolver = RefResolver(get_path_uri(schema_dir), schema)
            validate(instance=server_settings, schema=schema, resolver=resolver)
        except Exception as e:
            raise ConfigurationError(e)

    def load_settings(self, server_settings):
        if isinstance(server_settings, str):
            server_settings = json.loads(server_settings)
        self.valid_settings(server_settings)
        self.server_name = list(server_settings.keys())[0]
        self.localization = server_settings[self.server_name]['localization']
        self.services = server_settings[self.server_name]['services']
        self.port = server_settings[self.server_name]['port']
        self.image = server_settings[self.server_name]['type'].split('-')[1]
        if self.image not in self.image_support:
            raise ConfigurationError("Not support image {}. \n"
                                     "Support images: {}".format(self.image, self.image_support))

    def get_paths(self, *template_to_render):
        template_dir = self.settings.get("TEMPLATES_DIR", "")
        project_dir = self.settings.get("project_dir", "")
        if not template_dir or not project_dir:
            raise ValueError("Can't get Template or Project directory from setting")
        template_file = join(template_to_render[0], template_to_render[1])
        dst_file = join(template_to_render[0], template_to_render[2])
        template_file = string.Template(template_file).safe_substitute(prefix_dir=template_dir,
                                                                       name=self.__class__.__name__)
        dst_file = string.Template(dst_file).safe_substitute(prefix_dir=project_dir, name=self.server_name)
        return normpath(template_file), normpath(dst_file)

    def get_localizations(self, tz=True, distros=True, python=True):
        localization_distros_mirror = ""
        localization_tz = ""
        localization_python_mirror = ""
        if distros:
            local_distros_mirror = self.settings.get("LOCAL_{}_MIRROR".format(self.image.upper()), "")
            if not local_distros_mirror:
                raise ValueError("Can't get local distros mirror from setting")
            localization_distros_mirror = "# replace source list by local\n"
            if self.image == 'alpine':
                localization_distros_mirror += "    && cp /etc/apk/repositories /etc/apk/repositories.backup \\\n"
                localization_distros_mirror += "    && sed -i 's#http://dl-cdn.alpinelinux.org#{}#g' " \
                                               "/etc/apk/repositories \\".format(local_distros_mirror)
            else:
                localization_distros_mirror += "    && cp /etc/apt/sources.list /etc/apt/sources.list.backup \\\n"
                localization_distros_mirror += "    && sed -i 's#http://deb.debian.org#{}#g' " \
                                               "/etc/apt/sources.list \\".format(local_distros_mirror)
        if tz:
            # change local timezone
            local_tz = self.settings.get("LOCAL_TZ", "")
            if not local_tz:
                raise ValueError("Can't get local timezone from setting")
            localization_tz = "# change time to local \n"
            if self.image == 'alpine':
                localization_tz += "    && apk add --no-cache tzdata \\\n"
            localization_tz += "    && ln -snf /usr/share/zoneinfo/{} /etc/localtime && echo {} " \
                               "> /etc/timezone \\".format(local_tz, local_tz)
        if python:
            # change local python mirror
            local_python_mirror = self.settings.get("LOCAL_PYTHON_MIRROR", "")
            if not local_python_mirror:
                raise ValueError("Can't get python mirror from setting")
            localization_python_mirror = "# change pip source to local\n"
            localization_python_mirror += "    && pip3 config set global.index-url {} \\\n".format(local_python_mirror)
            localization_python_mirror += "    # install python packages"
        return {
            "tz": localization_tz,
            "distros": localization_distros_mirror,
            "python": localization_python_mirror
        }

    def check_duplicate_service_name(self):
        service_names = []
        for service_name, service in self.services.items():
            if service_name in service_names:
                raise ValueError("Wrong service_name")
            service_names.append(service_name)

    def render(self):
        raise NotImplementedError

    def generate_docker_compose_service(self):
        raise NotImplementedError

    def update_docker_compose(self):
        project_dir = self.settings.get('project_dir','')
        docker_compose_file = os.path.join(project_dir, 'docker-compose.yaml')
        with open(docker_compose_file, ) as f:
            docker_compose_content = yaml.safe_load(f)
        if 'services' not in docker_compose_content:
            raise ValueError('{} format wrong'.format(docker_compose_file))
        service_content = yaml.safe_load(self.generate_docker_compose_service())
        if not docker_compose_content['services']:
            docker_compose_content['services'] = {}
        docker_compose_content['services'][self.server_name] = service_content[self.server_name]
        with open(docker_compose_file, 'w') as f:
            document = yaml.dump(docker_compose_content, f, Dumper=PrettyDumper,
                                 default_flow_style=False, sort_keys=False)
