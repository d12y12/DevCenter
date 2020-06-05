#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import string
import os
from os.path import join, normpath, isfile, exists
import json
from shutil import ignore_patterns, copy2
from devspace.utils.misc import render_template, copytree
from devspace.servers import DevSpaceServer
import subprocess

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
    'Index': ('${prefix_dir}/${name}/web/html/', 'index.html.template', 'index.html'),
    # ${service_name}, ${consistency}, ${crontab}, ${repositories}, ${host}
    'Sqlite': ('${prefix_dir}/${name}/apps/database/', 'repository.sql.template', '${service_name}.sql'),
    # ${server_name}
    'DockerCompose': ('${prefix_dir}/${name}/', 'server.yaml.template',''),
}

APP_SRC = 'https://github.com/d12y12/GitMirror.git'


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
                dst = normpath(project_dir + '/' + self.server_name + '/web/statics/' + service_name)
                if not exists(dst):
                    os.makedirs(dst)
                for theme in ['light', 'dark']:
                    src = service['cgit_options']['logo'][theme]
                    dst_logo = join(dst, 'logo-%s.png' % theme)
                    copy2(src, dst_logo)

    def create_server_structure(self):
        template_srv_dir = join(self.settings.get("TEMPLATES_DIR", ""), self.__class__.__name__) if \
                                                self.settings.get("TEMPLATES_DIR", "") else ""
        prj_srv_dir = join(self.settings.get("project_dir", ""), self.server_name) if \
                                                self.settings.get("project_dir", "") else ""
        if not template_srv_dir or not prj_srv_dir:
            raise ValueError("Can't get Template or Project directory from setting")
        os.makedirs(prj_srv_dir, exist_ok=True)
        # copy /etc /var/www
        copytree(template_srv_dir, prj_srv_dir, ignore_patterns('*.template', 'apps'))
        # generate apps
        apps_dir = join(prj_srv_dir, 'apps')
        if not exists(apps_dir):
            os.mkdir(apps_dir)
            ret = subprocess.run(["git", "clone", APP_SRC, apps_dir], stdout=subprocess.DEVNULL)
            if ret.returncode != 0:
                raise RuntimeError("Clone app failde, please try render again")
        else:
            pass
        # make temp dir
        temp_dir = join(prj_srv_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(join(temp_dir, 'log'), exist_ok=True)
        os.makedirs(join(temp_dir, 'cache'), exist_ok=True)
        for sub_dir in os.listdir(temp_dir):
            sub_dir = join(temp_dir, sub_dir)
            for service_name, service in self.services.items():
                os.makedirs(join(sub_dir, service_name), exist_ok=True)
        # make data dir
        data_dir = join(prj_srv_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        for service_name, service in self.services.items():
                os.makedirs(join(data_dir, service_name), exist_ok=True)

    def render(self):
        service_names = []
        for service_name, service in self.services.items():
            if service_name in service_names:
                raise ValueError("Wrong service_name")
            service_names.append(service_name)
            if 'cgit_options' not in service or \
                not self._is_valid_cgit_options(service['cgit_options']):
                raise ValueError("Wrong cgit_options, service_name: " + service['service_name'])
        self.create_server_structure()
        self._render_dockerfile()
        self._render_cgit_config()
        self._render_nginx_default()
        self._render_nginx_config()
        self._rend_index()
        self._render_sqlite()
        self._copy_logo()


    def generate_docker_compose_service(self):
        template_file, dst_file = self.get_paths(*TEMPLATES_TO_RENDER['DockerCompose'])
        with open(template_file, 'rb') as fp:
            raw = fp.read().decode('utf8')
            content = string.Template(raw).safe_substitute(server_name=self.server_name,port=self.port)
        return content if content else ''
