class Project(object):
    def __init__(self, organization: str, project: str) -> None:
        self._organization = organization
        self._name = project

    @property
    def organization(self) -> str:
        return self._organization

    @property
    def name(self) -> str:
        return self._name
