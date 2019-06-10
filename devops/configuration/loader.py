from .configuration import Configuration


class Loader(object):
    config: Configuration

    @staticmethod
    def load_configuration(filename: str = 'config.json') -> Configuration:
        if not Loader.config:
            print(f'Loading configuration from {filename}')
            with open(filename) as config_file:
                import json
                data = json.load(config_file)
            Loader.config = Configuration(data)
        return Loader.config
