from dataclasses import dataclass
from datetime import datetime, time
from urllib import parse
from pytorjoman._backend import Model, _call, ModelList
from pytorjoman.errors import AlreadyExistError, NotAllowedError, NotFoundError, IncorrectPasswordError, TokenExpiredError, UnknownError, UnloggedInError

@dataclass
class Owner:
    id: int
    first_name: str


@dataclass
class Project(Model):
    id: int
    owner: Owner
    name: str
    created_at: datetime
    
    @staticmethod
    async def list_project(base_url: str, token: str, user: str = None, page: int = 1, page_size: int = 25):
        status, res = await _call(
            f'{base_url}/api/v1/projects/',
            "GET",
            params={
                "username": user,
                "page": page,
                "page_size": page_size,
            },
            token=token
        )
        match status:
            case 200:
                return ModelList(
                    res['count'],
                    dict(parse.parse_qsl(parse.urlsplit(res['next']).query)).get('page', None),
                    dict(parse.parse_qsl(parse.urlsplit(res['previous']).query)).get('page', None),
                    [
                        Project(
                            base_url,
                            'projects',
                            token,
                            p['id'],
                            Owner(
                                p['owner']['id'],
                                p['owner']['first_name']
                            ),
                            p['name'],
                            p['created_at']
                        )
                        for p in res['results']
                    ]
                )
            case 404:
                raise NotFoundError("User not found")
            case 422:
                raise ValueError("Incorrect value, please check username, page and page_size")
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    @staticmethod
    async def create_project(base_url: str, token: str, name: str):
        status, res = await _call(
            f'{base_url}/api/v1/projects/',
            data={
                "name": name
            },
            token=token
        )
        match status:
            case 200:
                return Project(
                    base_url,
                    'projects',
                    token,
                    res['id'],
                    Owner(
                        res['owner']['id'],
                        res['owner']['first_name']
                    ),
                    res['name'],
                    res['created_at']
                )
            case 409:
                raise AlreadyExistError()
            case 422:
                raise ValueError("Invalid page or page_size")
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    async def update(self, new_name: str):
        status, res = await _call(
            f'{self.base_url}/api/v1/projects/update',
            "PUT",
            data={
                "id": self.id,
                "new_name": new_name
            },
            token=self._access_token
        )
        match status:
            case 200:
                self.name = res['name']
            case 404:
                raise NotFoundError()
            case 401:
                raise TokenExpiredError()
            case 403:
                raise NotAllowedError()
            case 422:
                raise ValueError()
            case _:
                raise UnknownError()
