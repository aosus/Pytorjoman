from dataclasses import dataclass
from datetime import datetime
from urllib import parse
from pytorjoman._backend import Model, _call, ModelList
from pytorjoman.errors import AlreadyExistError, NotAllowedError, NotFoundError, TokenExpiredError, UnknownError, UnloggedInError
from pytorjoman.sections import Section

@dataclass
class Sentence(Model):
    id: int
    section: Section
    sentence: str
    created_at: datetime
    
    @staticmethod
    async def list_sentences(base_url: str, token: str, section: Section, page: int = 1, page_size: int = 25):
        status, res = await _call(
            f'{base_url}/api/v1/sentences/',
            "GET",
            params={
                "section": section.id,
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
                        Sentence(
                            base_url,
                            'sections',
                            token,
                            s['id'],
                            section,
                            s['sentence'],
                            s['created_at']
                        )
                        for s in res['results']
                    ]
                )
            case 404:
                raise NotFoundError()
            case 422:
                raise ValueError("Incorrect value, please check section")
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    @staticmethod
    async def create_sentence(base_url: str, token: str, section: Section, sentence: str):
        status, res = await _call(
            f'{base_url}/api/v1/sentences/',
            data={
                "sentence": sentence,
                "section_id": section.id,
            },
            token=token
        )
        match status:
            case 200:
                return Sentence(
                            base_url,
                            'sections',
                            token,
                            res['id'],
                            section,
                            res['sentence'],
                            res['created_at']
                        )
            case 409:
                raise AlreadyExistError()
            case 404:
                raise NotFoundError("No such section")
            case 422:
                raise ValueError("Invalid section")
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    async def update(self, new_sentence: str):
        status, res = await _call(
            f'{self.base_url}/api/v1/sentences/update',
            "PUT",
            data={
                "id": self.id,
                "new_sentence": new_sentence
            },
            token=self._access_token
        )
        match status:
            case 200:
                self.sentence = res['sentence']
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
