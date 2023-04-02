from dataclasses import dataclass
from datetime import datetime
from urllib import parse

import pytorjoman
from pytorjoman._backend import Model, ModelList, _call
from pytorjoman.errors import (
    AlreadyExistError,
    NotAllowedError,
    NotFoundError,
    TokenExpiredError,
    UnknownError,
)


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
    async def list_project(
        base_url: str,
        token: str,
        user: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ):
        status, res = await _call(
            f"{base_url}/api/v1/projects/",
            "GET",
            params={
                "username": user,
                "page": page,
                "page_size": page_size,
            },
            token=token,
        )
        match status:
            case 200:
                return ModelList(
                    res["count"],
                    int(
                        dict(parse.parse_qsl(parse.urlsplit(res["next"]).query)).get(
                            "page", None
                        )
                    ),
                    int(
                        dict(
                            parse.parse_qsl(parse.urlsplit(res["previous"]).query)
                        ).get("page", None)
                    ),
                    [
                        Project(
                            base_url,
                            "projects",
                            token,
                            p["id"],
                            Owner(p["owner"]["id"], p["owner"]["first_name"]),
                            p["name"],
                            p["created_at"],
                        )
                        for p in res["results"]
                    ],
                )
            case 404:
                raise NotFoundError("User not found")
            case 422:
                raise ValueError(
                    "Incorrect value, please check username, page and page_size"
                )
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    @staticmethod
    async def create_project(base_url: str, token: str, name: str):
        status, res = await _call(
            f"{base_url}/api/v1/projects/", data={"name": name}, token=token
        )
        match status:
            case 200:
                return Project(
                    base_url,
                    "projects",
                    token,
                    res["id"],
                    Owner(res["owner"]["id"], res["owner"]["first_name"]),
                    res["name"],
                    res["created_at"],
                )
            case 409:
                raise AlreadyExistError()
            case 422:
                raise ValueError("Invalid page or page_size")
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    @staticmethod
    async def get_project(base_url: str, token: str, project: int):
        status, res = await _call(
            f"{base_url}/api/v1/projects/{project}", "GET", with_auth=False
        )
        match status:
            case 200:
                return Project(
                    base_url,
                    "projects",
                    token,
                    res["id"],
                    Owner(res["owner"]["id"], res["owner"]["first_name"]),
                    res["name"],
                    res["created_at"],
                )
            case 404:
                raise NotFoundError("project not found")
            case _:
                raise UnknownError()

    async def update(self, new_name: str):
        status, res = await self._call(
            "update", "PUT", data={"id": self.id, "new_name": new_name}
        )
        match status:
            case 200:
                self.name = res["name"]
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

    async def create_section(self, name):
        section = await pytorjoman.Section.create_section(
            self.base_url, self._access_token, self, name
        )
        return section

    async def list_sections(self):
        sections = await pytorjoman.Section.list_sections(
            self.base_url, self._access_token, self
        )
        return sections
