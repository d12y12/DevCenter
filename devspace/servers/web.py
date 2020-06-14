#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import string
import os
from os.path import join, normpath, isfile, exists
import json
from shutil import ignore_patterns, copy2
from devspace.utils.misc import render_template, copytree
from devspace.servers import DevSpaceServer
import yaml


TEMPLATES_MAPPING = {
    # ${maintainer}, ${localization}, ${image}, ${port}
    "Dockerfile": ("${TEMPLATES_DIR}/Web/Dockerfile-${image}.template",
                   "${project_dir}/servers/Web/Dockerfile"),
    # ${title}, ${description}, ${max-repo-count},${service_name}, ${host}
    "Cgit_Config": ('${TEMPLATES_DIR}/Web/config/cgit/cgitrc.template',
                    '${project_dir}/servers/Web/config/cgit/${service_name}.cgit.com'),
    # ${nginx_service} ${port}
    "Nginx_Default": ('${TEMPLATES_DIR}/Web/config/nginx/default.template',
                      '${project_dir}/servers/Web/config/nginx/default'),
    # ${service_name}
    "Nginx_Config": ('${TEMPLATES_DIR}/Web/config/nginx/cgit.template',
                     '${project_dir}/servers/Web/config/nginx/${service_name}.cgit.com'),
    # ${services}
    'Index': ('${TEMPLATES_DIR}/Web/www/index.html.template',
              '${project_dir}/www/index.html'),
    # ${server_name}
    'DockerCompose': ('${TEMPLATES_DIR}/Web/server.yaml.template', ''),
}


def _is_valid_cgit_options(cgit_options):
    if 'logo' in cgit_options:
        if not isfile(cgit_options['logo']['light']):
            print("Error: logo light file not exist")
            return False
        if not isfile(cgit_options['logo']['dark']):
            print("Error: logo dark file not exist")
            return False
    return True


class Web(DevSpaceServer):
    type = 'Web'
    image_support = ['debian', 'alpine']

    def __init__(self, server_settings=None):
        self.host = ""
        self.port = -1
        self.cgit = False
        super().__init__(server_settings)
        self.templates_mapping = json.loads(string.Template(json.dumps(TEMPLATES_MAPPING)).safe_substitute(
            TEMPLATES_DIR=self.settings.get("TEMPLATES_DIR", "").replace("\\", "/"),
            image=self.image,
            project_dir=self.settings['project']['path'].replace("\\", "/")
        ))

    def load_settings(self):
        super().load_settings()
        server_settings = self.settings['servers']
        self.host = server_settings[self.server_name]['host']
        self.port = server_settings[self.server_name]['port']
        if self.settings['services']:
            for service_name, service_setting in self.settings['services'].items():
                if self.__class__.__name__ in service_setting:
                    self.services[service_name] = service_setting[self.__class__.__name__]
                    if 'cgit_options' in service_setting[self.__class__.__name__].keys():
                        self.cgit = True
                        if not _is_valid_cgit_options(service_setting[self.__class__.__name__]['cgit_options']):
                            raise ValueError("Wrong cgit_options, service_name: {}".format(service_name))

    def dockerfile(self, tz=True, distros=True, python=True):
        # ${port}
        super().dockerfile(tz, distros, python)
        dst_file = self.templates_mapping['Dockerfile'][1]
        render_template(dst_file, dst_file, port=self.port)

    def cgit_config(self):
        # ${title}, ${description}, ${max-repo-count},${service_name}
        for service_name, service in self.services.items():
            if 'cgit_options' in service.keys():
                host = '{}:{}'.format(self.host, self.port)
                schema = 'http'
                host = host if host.startswith('http') else schema+'://{}'.format(host)
                title = service['cgit_options']['title']
                description = service['cgit_options']['description']
                max_repo_count = service['cgit_options']['max-repo-count']
                template_file = self.templates_mapping['Cgit_Config'][0]
                dst_file = self.templates_mapping['Cgit_Config'][1]
                dst_file = string.Template(dst_file).safe_substitute(service_name=service_name)
                render_template(template_file, dst_file, title=title, description=description,
                                max_repo_count=max_repo_count, service_name=service_name, host=host)

    def nginx_default(self):
        # ${nginx_service} ${port}
        template_file = self.templates_mapping['Nginx_Default'][0]
        dst_file = self.templates_mapping['Nginx_Default'][1]
        nginx_service = ""
        for service_name, service in self.services.items():
            if 'cgit_options' in service.keys():
                nginx_service += "\n  location /%s/ {\n" \
                                 "      proxy_pass http://%s.cgit.com:%s/;\n" \
                                 "  }" % (service_name, service_name, str(self.port))
            else:
                index = "index index.html;"
                if 'autoindex' in service.keys() and service['autoindex']:
                    index = "autoindex on;"
                nginx_service += "\n  location /%s/ {\n" \
                                 "      root  /var/www/services/%s;\n" \
                                 "      %s\n" \
                                 "  }" % (service_name, service_name, index)

        render_template(template_file, dst_file, nginx_service=nginx_service, port=self.port)

    def nginx_cgit_config(self):
        # ${service_name} ${port}
        for service_name, service in self.services.items():
            if 'cgit_options' in service.keys():
                template_file = self.templates_mapping['Nginx_Config'][0]
                dst_file = self.templates_mapping['Nginx_Config'][1]
                dst_file = string.Template(dst_file).safe_substitute(service_name=service_name)
                render_template(template_file, dst_file, service_name=service_name, port=self.port)

    def index(self):
        template_file = self.templates_mapping['Index'][0]
        dst_file = self.templates_mapping['Index'][1]
        services = "<li>Doc services\n<ul>"
        cgit_services = "<li>Cgit services\n<ul>"
        for service_name, service in self.services.items():
            if 'cgit_options' in service.keys():
                cgit_services += '<li><a href="/%s">%s</a></li>\n' % (service_name, service_name)
            else:
                services += '<li><a href="/%s">%s</a></li>\n' % (service_name, service_name)
        services += "</ul>\n</li>\n" + cgit_services + "</ul>\n</li>\n"
        render_template(template_file, dst_file, services=services)

    def copy_logo(self):
        project_dir = self.settings['project']['path']
        if not project_dir:
            raise ValueError("Can't get Template or Project directory from setting")
        for service_name, service in self.services.items():
            if 'cgit_options' in service.keys() and 'logo' in service['cgit_options']:
                dst = normpath(project_dir + '/www/cgit/' + service_name)
                if not exists(dst):
                    os.makedirs(dst)
                for theme in ['light', 'dark']:
                    src = service['cgit_options']['logo'][theme]
                    dst_logo = join(dst, 'logo-%s.png' % theme)
                    copy2(src, dst_logo)

    def create_server_structure(self):
        template_srv_dir = join(self.settings.get("TEMPLATES_DIR", ""), self.__class__.__name__) if \
                                                self.settings.get("TEMPLATES_DIR", "") else ""
        prj_srv_dir = join(self.settings['project']['path'], "servers", self.server_name) if \
                                                self.settings['project']['path'] else ""
        if not template_srv_dir or not prj_srv_dir:
            raise ValueError("Can't get Template or Project directory from setting")
        os.makedirs(prj_srv_dir, exist_ok=True)
        copytree(template_srv_dir, prj_srv_dir, ignore_patterns('*.template', 'www'))
        # make www
        www_dir = self.settings.get("SHARED_WEB", "")
        os.makedirs(www_dir, exist_ok=True)
        if self.cgit:
            cgit_dir = self.settings.get("CGIT_STATICS", "")
            copytree(join(template_srv_dir, "www", "cgit"), cgit_dir)
        # make log root
        log_dir = join(self.settings.get("SHARED_LOG", ""), self.server_name)
        os.makedirs(log_dir, exist_ok=True)
        # make data root
        data_dir = self.settings.get("SHARED_DATA", "")
        os.makedirs(data_dir, exist_ok=True)
        for service_name, service in self.services.items():
            if 'cgit_options' in service.keys():
                # make cgit log
                os.makedirs(join(log_dir, service_name), exist_ok=True)
            else:
                # make no-cgit www
                os.makedirs(join(www_dir, 'services', service_name), exist_ok=True)
            # make data
            os.makedirs(join(data_dir, service_name), exist_ok=True)

    def render(self):
        print("render web")
        self.create_server_structure()
        self.dockerfile()
        self.cgit_config()
        self.nginx_default()
        self.nginx_cgit_config()
        self.index()
        self.copy_logo()

    def generate_docker_compose_service(self):
        template_file = self.templates_mapping['DockerCompose'][0]
        with open(template_file, 'rb') as fp:
            raw = fp.read().decode('utf8')
            content = string.Template(raw).safe_substitute(
                server_name=(self.settings['project']['name'] +'_' + self.server_name).lower(),
                port=self.port)
        service_content = yaml.safe_load(content)
        for service_name, service in self.services.items():
            if 'cgit_options' in service.keys():
                service_content['web']['volumes'].append('./data/{}:/srv/git/{}:ro'.format(service_name, service_name))
        content = yaml.safe_dump(service_content)
        return content if content else ''
