#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import string
import os
from os.path import join, normpath, isfile, exists
import json
from shutil import ignore_patterns, copy2
from devspace.utils.misc import render_template, copytree
from devspace.servers import DevSpaceServer

TEMPLATES_TO_RENDER = {
    # ${maintainer}, ${localization}
    'Dockerfile': ('${prefix_dir}/${name}/', 'Dockerfile.template', 'Dockerfile'),
    # ${title}, ${description}, ${max-repo-count},${service_name}, ${host}
    'Cgit_Config': ('${prefix_dir}/${name}/config/cgit/', 'cgitrc.template', '${service_name}.mirror.com'),
    # ${nginx_service}
    'Nginx_Default': ('${prefix_dir}/${name}/config/nginx/', 'default.template', 'default'),
    # ${service_name}
    'Nginx_Config': ('${prefix_dir}/${name}/config/nginx/', 'mirror.template', '${service_name}.mirror.com'),
    # ${services}
    'Index': ('${prefix_dir}/${name}/var/www/html/', 'index.html.template', 'index.html'),
    # ${service_name}, ${consistency}, ${crontab}, ${repositories}, ${host}
    'Sqlite': ('${prefix_dir}/${name}/apps/database/', 'repository.sql.template', '${service_name}.sql'),
    # ${server_name}
    'DockerCompose': ('${prefix_dir}/${name}/', 'server.yaml.template',''),
}


class GitMirror(DevSpaceServer):
    type = 'GitMirror'
    support_repository_type = ['cgit', 'github']

    def _is_valid_cgit_options(self, cgit_options):
        if 'logo' in cgit_options:
            if not isfile(cgit_options['logo']['light']):
                print("Error: logo light file not exist")
                return False
            if not isfile(cgit_options['logo']['dark']):
                print("Error: logo dark file not exist")
                return False
        return True

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

    def _render_dockerfile(self):
        # ${maintainer}, ${localization}
        template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['Dockerfile'])
        maintainer = 'LABEL maintainer="%s"' % self.author if self.author else ""
        localization_str = ""
        if self.localization:
            local_tz = self.settings.get("LOCAL_TZ", "")
            local_mirror = self.settings.get("LOCAL_DEBIAN_MIRROR", "")
            if not local_tz or not local_mirror:
                raise ValueError("Can't get TZ or Local package mirror from setting")
            localization_str = "# replace source list by China local\n" \
                               "    && cp /etc/apt/sources.list /etc/apt/sources.list.backup \\ \n" \
                               "    && sed -i 's#http://deb.debian.org#%s#g' /etc/apt/sources.list \\ \n" \
                               "# change time to local \n" \
                               "    && ln -snf /usr/share/zoneinfo/%s /etc/localtime && echo %s > /etc/timezone \\" \
                                % (local_mirror, local_tz, local_tz)
        render_template(template_file, dst_file, localization=localization_str, maintainer=maintainer, port=self.port)

    def _render_cgit_config(self):
        # ${title}, ${description}, ${max-repo-count},${service_name}
        for service_name, service in self.services.items():
            host = '{}:{}'.format(self.host, self.port)
            schema = 'http'
            host = host if host.startswith('http') else schema+'://{}'.format(host)
            title = service['cgit_options']['title']
            description = service['cgit_options']['description']
            max_repo_count = service['cgit_options']['max-repo-count']
            template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['Cgit_Config'])
            dst_file = string.Template(dst_file).safe_substitute(service_name=service_name)
            render_template(template_file, dst_file, title=title, description=description,
                            max_repo_count=max_repo_count, service_name=service_name, host=host)

    def _render_nginx_default(self):
        # ${nginx_service}
        template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['Nginx_Default'])
        nginx_service = ""
        for service_name, service in self.services.items():
            nginx_service += "\n  location /%s/ {\n" \
                             "      proxy_pass http://%s.mirror.com:8080/;\n" \
                             "  }" % (service_name, service_name)
        render_template(template_file, dst_file, nginx_service=nginx_service)

    def _render_nginx_config(self):
        # ${service_name}
        for service_name, service in self.services.items():
            template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['Nginx_Config'])
            dst_file = string.Template(dst_file).safe_substitute(service_name=service_name)
            render_template(template_file, dst_file, service_name=service_name)

    def _rend_index(self):
        template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['Index'])
        services = ""
        for service_name, service in self.services.items():
            services += '<li><a href="/%s">%s</a></li>\n' % (service_name, service_name)
        render_template(template_file, dst_file, services=services)

    def _render_sqlite(self):
        # ${title}, ${description}, ${max-repo-count},${service_name}
        host = '{}:{}'.format(self.host, self.port)
        for service_name, service in self.services.items():
            consistency = 1 if service['synchronization']['consistency'] else 0
            crontab = service['synchronization']['crontab']
            repositories = json.dumps(service['repositories'])
            template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['Sqlite'])
            dst_file = string.Template(dst_file).safe_substitute(service_name=service_name)
            render_template(template_file, dst_file, consistency=consistency, crontab=crontab,
                            repositories=repositories, service_name=service_name, host=host)

    def _copy_logo(self):
        project_dir = self.settings.get("project_dir", "")
        if not project_dir:
            raise ValueError("Can't get Template or Project directory from setting")
        for service_name, service in self.services.items():
            if 'logo' in service['cgit_options']:
                dst = normpath(project_dir + '/' + self.server_name + '/var/www/statics/' + service_name)
                if not exists(dst):
                    os.makedirs(dst)
                for theme in ['light', 'dark']:
                    src = service['cgit_options']['logo'][theme]
                    dst_logo = join(dst, 'logo-%s.png' % theme)
                    copy2(src, dst_logo)

    def _copy_app(self):
        project_dir = self.settings.get("project_dir", "")
        apps_dir = self.settings.get("APPS_DIR", "")
        if not project_dir or not apps_dir:
            raise ValueError("Can't get Template or Apps directory from setting")
        apps = self.__class__.__name__
        apps_dir = normpath(apps_dir + '/' + apps)
        dst_apps_dir = normpath(project_dir + '/' + self.server_name + '/apps')
        copytree(apps_dir, dst_apps_dir, ignore_patterns('database', '__pycache__'))

    def _mkdir_in_temp(self):
        project_dir = self.settings.get("project_dir", "")
        dst_dir = normpath(project_dir + '/' + self.server_name + '/temp')
        for sub_dir in os.listdir(dst_dir):
            sub_dir = join(dst_dir, sub_dir)
            for service_name, service in self.services.items():
                if not exists(join(sub_dir, service_name)):
                    os.mkdir(join(sub_dir, service_name))

    def _mkdir_in_data(self):
        project_dir = self.settings.get("project_dir", "")
        dst_dir = normpath(project_dir + '/' + self.server_name + '/data')
        for service_name, service in self.services.items():
            if not exists(join(dst_dir, service_name)):
                os.mkdir(join(dst_dir, service_name))

    def render(self):
        service_names = []
        for service_name, service in self.services.items():
            if service_name in service_names:
                raise ValueError("Wrong service_name")
            service_names.append(service_name)
            if 'cgit_options' not in service or \
                not self._is_valid_cgit_options(service['cgit_options']):
                raise ValueError("Wrong cgit_options, service_name: " + service['service_name'])
        template_dir = self.settings.get("TEMPLATES_DIR", "")
        project_dir = self.settings.get("project_dir", "")
        if not template_dir or not project_dir:
            raise ValueError("Can't get Template or Project directory from setting")
        server_dir = join(project_dir, self.server_name)
        if not exists(server_dir):
            os.makedirs(server_dir)
        template_dir = join(template_dir, self.__class__.__name__)
        copytree(template_dir, server_dir, ignore_patterns('*.template'))
        self._render_dockerfile()
        self._render_cgit_config()
        self._render_nginx_default()
        self._render_nginx_config()
        self._rend_index()
        self._render_sqlite()
        self._copy_logo()
        self._copy_app()
        self._mkdir_in_temp()


    def generate_docker_compose_service(self):
        template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['DockerCompose'])
        with open(template_file, 'rb') as fp:
            raw = fp.read().decode('utf8')
            content = string.Template(raw).safe_substitute(server_name=self.server_name,port=self.port)
        return content if content else ''
