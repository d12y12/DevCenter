import os
import json
import yaml
from jsonschema import validate, RefResolver
from devspace.settings import Settings
from devspace.exceptions import ConfigurationError
from devspace.utils.misc import get_path_uri, get_project_dir


class PrettyDumper(yaml.SafeDumper):
    yaml.SafeDumper.add_representer(
        type(None),
        lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:null', '')
    )

    def increase_indent(self, flow=False, indentless=False):
        return super(PrettyDumper, self).increase_indent(flow, False)


class DevSpaceServer:

    type = ''

    def __init__(self, server_settings=None):
        self.server_name = ''
        self.port = -1
        self.localization = False
        self.services = []
        self.settings = Settings()
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
