from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib import parse
import pytorjoman
from pytorjoman._backend import Model, ModelList, _call
from pytorjoman.errors import (AlreadyExistError, NotAllowedError,
                               NotFoundError, TokenExpiredError, UnknownError,
                               UnloggedInError)
from pytorjoman.projects import Owner

@dataclass
class Translation(Model):
    id: int
    translator: Optional[Owner]
    sentence: pytorjoman.Sentence
    translation: str
    voters: Optional[list[Owner]]
    is_approved: bool
    created_at: datetime
    
    @staticmethod
    async def list_translations(base_url: str, token: str, sentence: pytorjoman.Sentence, page: int = 1, page_size: int = 25):
        """Get Sentence's translations. 
        
        it doesn't return voters due to API limitations, to get voters please use get_voters function instead
        """
        status, res = await _call(
            f'{base_url}/api/v1/translations/',
            "GET",
            params={
                "sentence": sentence.id,
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
                        Translation(
                            base_url,
                            'translations',
                            token,
                            t['id'],
                            Owner(
                                t['translator']['id'],
                                t['translator']['first_name']
                            ) if t.get('translator') else None,
                            sentence,
                            t['translation'],
                            None,
                            t['is_approved'],
                            t['created_at']
                        )
                        for t in res['results']
                    ]
                )
            case 404:
                raise NotFoundError()
            case 422:
                raise ValueError("Incorrect value, please check sentence")
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    @staticmethod
    async def create_translation(base_url: str, token: str, sentence: pytorjoman.Sentence, translation: str):
        status, res = await _call(
            f'{base_url}/api/v1/translations/',
            data={
                "translation": translation,
                "sentence_id": sentence.id,
            },
            token=token
        )
        match status:
            case 200:
                return Translation(
                            base_url,
                            'translations',
                            token,
                            res['id'],
                            Owner(
                                res['translator']['id'],
                                res['translator']['first_name']
                            ) if res.get('translator') else None,
                            sentence,
                            res['translation'],
                            [
                                Owner(
                                    v['id'],
                                    v['first_name']
                                )
                                for v in res['voters']
                            ],
                            res['is_approved'],
                            res['created_at']
                        )
            case 409:
                raise AlreadyExistError()
            case 404:
                raise NotFoundError("No such sentence")
            case 422:
                raise ValueError("Invalid sentence")
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()
    
    @staticmethod
    async def get_translation(base_url: str, token: str, translation: int):
        status, res = await _call(
            f'{base_url}/api/v1/translations/{translation}',
            "GET",
            with_auth=False
        )
        match status:
            case 200:
                return Translation(
                            base_url,
                            'translations',
                            token,
                            res['id'],
                            Owner(
                                res['translator']['id'],
                                res['translator']['first_name']
                            ) if res.get('translator') else None,
                            pytorjoman.Sentence(
                                base_url,
                                "sentences",
                                token,
                                res['sentence']['id'],
                                await pytorjoman.Section.get_section(base_url, token, res['sentence']['section']),
                                res['sentence']['sentence'],
                                res['sentence']['created_at']
                            ),
                            res['translation'],
                            [
                                Owner(
                                    v['id'],
                                    v['first_name']
                                )
                                for v in res['voters']
                            ],
                            res['is_approved'],
                            res['created_at']
                        )
            case 404:
                raise NotFoundError("Translation not found")
            case _:
                raise UnknownError()

    async def get_voters(self):
        status, res = await self._call(
            f"{self.id}",
            "GET",
        )
        match status:
            case 200:
                self.voters = [
                    Owner(
                        v['id'],
                        v['first_name']
                    )
                    for v in res['voters']
                ]
            case 404:
                raise NotFoundError()
            case 401:
                raise TokenExpiredError()
            case 422:
                raise ValueError()
            case _:
                raise UnknownError()
