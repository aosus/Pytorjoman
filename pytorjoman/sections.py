from dataclasses import dataclass
from datetime import datetime, time
from urllib import parse
import pytorjoman
from pytorjoman._backend import Model, ModelList, _call
from pytorjoman.errors import (AlreadyExistError, IncorrectPasswordError,
                               NotAllowedError, NotFoundError,
                               TokenExpiredError, UnknownError,
                               UnloggedInError)


@dataclass
class Section(Model):
    id: int
    project: pytorjoman.Project
    name: str
    created_at: datetime
    
    @staticmethod
    async def list_sections(base_url: str, token: str, project: pytorjoman.Project):
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
    async def create_section(base_url: str, token: str, project: pytorjoman.Project, name: str):
        status, res = await _call(
            f'{base_url}/api/v1/sections/',
            data={
                "name": name,
                "project_id": project.id,
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
        status, res = await self._call(
            'update',
            "PUT",
            data={
                "id": self.id,
                "new_name": new_name
            }
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

    async def create_sentence(self, sentence):
        sentence = await pytorjoman.Sentence.create_sentence(self.base_url, self._access_token, self, sentence)
        return sentence
    
    async def list_sentences(self, page: int = 1, page_size = 25):
        sentences = await pytorjoman.Sentence.list_sentences(
            self.base_url,
            self._access_token,
            self,
            page,
            page_size
        )
        return sentences