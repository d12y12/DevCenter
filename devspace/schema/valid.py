import json
from jsonschema import validate, RefResolver


def valid_project_only():
    with open('project_example.json', 'r') as f:
        data = json.load(f)
    with open('project_only_schema.json', 'r') as f:
        schema = json.load(f)
    validate(instance=data, schema=schema)
    print("Project only OK!")


def valid_project():
    with open('project_example.json', 'r') as f:
        data = json.load(f)
    with open('project_schema.json', 'r') as f:
        schema = json.load(f)
    resolver = RefResolver("file:///E:/Git/DevSpace/definitions/", schema)
    validate(instance=data, schema=schema, resolver=resolver)


def valid_gitmirror():
    with open('project_example.json', 'r') as f:
        data = json.load(f)['servers']['demo']
    with open('gitmirror_schema.json', 'r') as f:
        schema = json.load(f)
    validate(instance=data, schema=schema)
    print("GitMirror OK!")

if __name__ == '__main__':
    # valid_project_only()
    # valid_gitmirror()
    valid_project()

