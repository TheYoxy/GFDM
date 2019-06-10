from .configuration import Configuration


def load_configuration(filename: str = 'config.json') -> Configuration:
    print(f'Loading configuration from {filename}')
    with open(filename) as config_file:
        import json
        data = json.load(config_file)
    return Configuration(data)
