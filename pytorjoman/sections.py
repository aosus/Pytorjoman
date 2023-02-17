from dataclasses import dataclass
from datetime import datetime, time
from urllib import parse
from pytorjoman._backend import Model, _call, ModelList
from pytorjoman.errors import AlreadyExistError, NotAllowedError, NotFoundError, IncorrectPasswordError, TokenExpiredError, UnknownError, UnloggedInError
from pytorjoman.projects import Project

@dataclass
class Owner:
    id: int
    first_name: str


@dataclass
class Section(Model):
    id: int
    project: Project
    name: str
    created_at: datetime
    
    @staticmethod
    async def list_sections(base_url: str, token: str, project: Project):
        status, res = await _call(
            f'{base_url}/api/v1/sections/',
            "GET",
            params={
                "project": project.id,
            },
            token=token
        )
        match status:
            case 200:
                return [
                        Section(
                            base_url,
                            'projects',
                            token,
                            s['id'],
                            project,
                            s['name'],
                            s['created_at']
                        )
                        for s in res
                    ]
            case 404:
                raise NotFoundError()
            case 422:
                raise ValueError("Incorrect value, please check project")
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    @staticmethod
    async def create_section(base_url: str, token: str, project: Project, name: str):
        status, res = await _call(
            f'{base_url}/api/v1/sections/',
            data={
                "name": name,
                "project": project.id,
            },
            token=token
        )
        match status:
            case 200:
                return Section(
                            base_url,
                            'projects',
                            token,
                            res['id'],
                            project,
                            res['name'],
                            res['created_at']
                        )
            case 409:
                raise AlreadyExistError()
            case 404:
                raise NotFoundError("No such project")
            case 422:
                raise ValueError("Invalid project")
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    async def update(self, new_name: str):
        status, res = await _call(
            f'{self.base_url}/api/v1/sections/update',
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
