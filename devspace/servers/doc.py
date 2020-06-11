#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import string
import os
from os.path import join, isdir
from shutil import ignore_patterns
from devspace.utils.misc import render_template, copytree
from devspace.servers import DevSpaceServer
import subprocess

TEMPLATES_TO_RENDER = {
    # ${maintainer}, ${localization}
    'Dockerfile': ('${prefix_dir}/${name}/', 'Dockerfile-${image}.template', 'Dockerfile'),
    # ${port}
    'Nginx_Default': ('${prefix_dir}/${name}/config/nginx/', 'default.template', 'default'),
    # ${services}
    'Index': ('${prefix_dir}/${name}/web/html/', 'index.html.template', 'index.html'),
    # ${server_name}
    'DockerCompose': ('${prefix_dir}/${name}/', 'server.yaml.template',''),
}


class Doc(DevSpaceServer):
    type = 'Doc'
    image_support = ['alpine']

    def _render_dockerfile(self):
        # ${image} ${maintainer}, ${port}
        # ${localization_distros_mirror}, ${localization_tz}, ${localization_python_mirror}
        template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['Dockerfile'])
        image = self.settings.get("IMAGE_{}".format(self.image.upper()), "")
        if not image:
            raise ValueError("Can't get image base from setting")
        maintainer = 'LABEL maintainer="%s"' % self.author if self.author else ""
        localization_distros_mirror = ""
        localization_tz = ""
        localization_python_mirror = ""
        if self.localization:
            localizations_strings = self.get_localizations()
            localization_tz = localizations_strings['tz']
            localization_distros_mirror = localizations_strings['distros']
            localization_python_mirror = localizations_strings['python']
        docbook_builder = ""
        sphnix_builder = ""
        builder = []
        for service_name, service in self.services.items():
            builder.append(service['builder'])
        if "docbook" in builder:
            docbook_builder = "libxslt \\"
        if "sphnix" in builder:
            sphnix_builder = "&& pip3 install --no-cache-dir sphinx sphinx_rtd_theme recommonmark \\"
        template_file = string.Template(template_file).safe_substitute(image=self.image)
        render_template(template_file, dst_file, image=image, maintainer=maintainer, port=self.port,
                        localization_distros_mirror=localization_distros_mirror, localization_tz=localization_tz,
                        localization_python_mirror=localization_python_mirror, docbook_builder=docbook_builder,
                        sphnix_builder=sphnix_builder)

    def _render_nginx_default(self):
        # ${port}
        template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['Nginx_Default'])
        render_template(template_file, dst_file, port=self.port)

    def _rend_index(self):
        template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['Index'])
        services = ""
        for service_name, service in self.services.items():
            services += '<li><a href="/%s">%s</a></li>\n' % (service_name, service_name)
        render_template(template_file, dst_file, services=services)

    def create_server_structure(self):
        template_srv_dir = join(self.settings.get("TEMPLATES_DIR", ""), self.__class__.__name__) if \
                                                self.settings.get("TEMPLATES_DIR", "") else ""
        prj_srv_dir = join(self.settings.get("project_dir", ""), self.server_name) if \
                                                self.settings.get("project_dir", "") else ""
        if not template_srv_dir or not prj_srv_dir:
            raise ValueError("Can't get Template or Project directory from setting")
        os.makedirs(prj_srv_dir, exist_ok=True)
        copytree(template_srv_dir, prj_srv_dir, ignore_patterns('*.template'))
        # make log dir
        log_dir = join(prj_srv_dir, 'log')
        os.makedirs(log_dir, exist_ok=True)
        # make data dir
        data_dir = join(prj_srv_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        for service_name, service in self.services.items():
            service_dir = join(data_dir, service_name)
            os.makedirs(service_dir, exist_ok=True)
            if len(os.listdir(service_dir)) == 0 and service['source']:
                if isdir(service['source']):
                    copytree(service['source'], service_dir)
                else:
                    ret = subprocess.run(["git", "clone", "--mirror", service['source'], service_dir], stdout=subprocess.DEVNULL)
                    if ret.returncode != 0:
                        raise RuntimeError("can't clone {}".format(service['source']))
            else:
                pass

        html_dir = join(prj_srv_dir, 'web', 'html')
        for service_name, service in self.services.items():
            service_dir = join(html_dir, service_name)
            os.makedirs(service_dir, exist_ok=True)

    def render(self):
        self.check_duplicate_service_name()
        self.create_server_structure()
        self._render_dockerfile()
        self._render_nginx_default()
        self._rend_index()

    def generate_docker_compose_service(self):
        template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['DockerCompose'])
        with open(template_file, 'rb') as fp:
            raw = fp.read().decode('utf8')
            content = string.Template(raw).safe_substitute(server_name=self.server_name,port=self.port)
        return content if content else ''
