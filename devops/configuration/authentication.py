class Authentication(object):
    def __init__(self, username: str, personal_access_token: str) -> None:
        super().__init__()
        self._username = username
        self._personal_access_token = personal_access_token

    @property
    def username(self) -> str:
        return self._username

    @property
    def personal_access_token(self) -> str:
        return self._personal_access_token

    @property
    def tuple(self) -> (str, str):
        return self.username, self.personal_access_token
