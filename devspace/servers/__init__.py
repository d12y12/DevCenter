#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import yaml
import string
from os.path import join, normpath
from devspace.exceptions import ConfigurationError
from devspace.utils.misc import render_template


class PrettyDumper(yaml.SafeDumper):
    yaml.SafeDumper.add_representer(
        type(None),
        lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:null', '')
    )

    def increase_indent(self, flow=False, indentless=False):
        return super(PrettyDumper, self).increase_indent(flow, False)


class DevSpaceServer:

    type = ''
    image_support = ['debian', 'alpine']

    def __init__(self, project_settings=None):
        self.server_name = self.__class__.__name__
        self.image = ''
        self.services = {}
        self.localization = False
        if not project_settings:
            raise ValueError("project setting is need for init server")
        self.settings = project_settings
        self.templates_mapping = {}
        self.load_settings()

    def load_settings(self):
        server_settings = self.settings['servers']
        self.localization = server_settings[self.server_name]['localization']
        self.image = server_settings[self.server_name]['type']
        if self.image not in self.image_support:
            raise ConfigurationError("Not support image {}. \n"
                                     "Support images: {}".format(self.image, self.image_support))

    def dockerfile(self, tz=True, distros=True, python=True):
        # ${image} ${maintainer}, ${localization_distros_mirror}, ${localization_tz}, ${localization_python_mirror}
        template_file = self.templates_mapping['Dockerfile'][0]
        dst_file = self.templates_mapping['Dockerfile'][1]
        image = self.settings.get("IMAGE_{}".format(self.image.upper()), "")
        if not image:
            raise ValueError("Can't get image base from setting")
        maintainer = 'LABEL maintainer="%s"' % self.settings.get("maintainer", "") if \
            self.settings.get("maintainer", "") else ""
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

        template_file = string.Template(template_file).safe_substitute(image=self.image)
        render_template(template_file, dst_file, image=image, maintainer=maintainer,
                        localization_distros_mirror=localization_distros_mirror, localization_tz=localization_tz,
                        localization_python_mirror=localization_python_mirror)

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
        docker_compose_content['services'][self.server_name.lower()] = service_content[self.server_name.lower()]
        with open(docker_compose_file, 'w') as f:
            document = yaml.dump(docker_compose_content, f, Dumper=PrettyDumper,
                                 default_flow_style=False, sort_keys=False)
