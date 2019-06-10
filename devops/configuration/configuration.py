from .authentication import Authentication
from .project import Project


class Configuration(object):
    def __init__(self, obj):
        self._authentication = Authentication(obj['Authentication']['Username'], obj['Authentication']['PersonalAccessToken'])
        self._project = Project(obj['Project']['Organization'], obj['Project']['Name'])

    @property
    def authentication(self) -> Authentication:
        return self._authentication

    @property
    def project(self) -> Project:
        return self._project
