from dataclasses import dataclass
from datetime import time
from typing import Union

import pytorjoman
from pytorjoman._backend import Model, _call
from pytorjoman.errors import (
    AlreadyExistError,
    IncorrectPasswordError,
    NotFoundError,
    TokenExpiredError,
    UnknownError,
)


@dataclass
class Account(Model):
    id: int
    first_name: str
    last_name: str
    email: str
    username: str
    send_time: time
    number_of_words: int
    _refresh_token: str

    async def update(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        send_time: time | None = None,
        number_of_words: int | None = None,
    ) -> None:
        data = {}
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        if send_time:
            data["send_time"] = send_time
        if number_of_words:
            data["number_of_words"] = number_of_words
        status, res = await self._call("update", "PUT", data=data)
        match status:
            case 200:
                self.id = res["id"]
                self.first_name = res["first_name"]
                self.last_name = res["last_name"]
                self.email = res["email"]
                self.username = res["username"]
                self.send_time = res["send_time"]
                self.number_of_words = res["number_of_words"]
                self._access_token = res["tokens"]["access"]
                self._refresh_token = res["tokens"]["refresh"]
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    async def refresh_token(self):
        status, res = await self._call(
            f"refresh/{self._refresh_token}", "GET", with_auth=False
        )
        match status:
            case 200:
                self._access_token = res["access"]
                self._refresh_token = res["refresh"]
            case 401:
                raise TokenExpiredError()
            case _:
                return UnknownError()

    async def change_password(self, current_password: str, new_password: str):
        status, res = await self._call(
            "change-password",
            data={"current_password": current_password, "new_password": new_password},
        )
        match status:
            case 200:
                self._access_token = res["access"]
                self._refresh_token = res["refresh"]
            case 401:
                match res["detail"]:
                    case "incorrect_password":
                        raise IncorrectPasswordError()
                    case "Unauthorized":
                        raise TokenExpiredError()
            case 422:
                raise ValueError("password lenght must be between 8 and 50")
            case _:
                return UnknownError()

    async def create_project(self, name):
        project = await pytorjoman.Project.create_project(
            self.base_url, self._access_token, name
        )
        return project

    async def list_projects(self, page: int = 1, page_size=25, mine: bool = True):
        projects = await pytorjoman.Project.list_project(
            self.base_url,
            self._access_token,
            self.username if mine else None,
            page,
            page_size,
        )
        return projects

    async def get_sentences_for_user(
        self,
        project: Union[int, "pytorjoman.Project", None] = None,
        section: Union[int, "pytorjoman.Section", None] = None,
    ) -> list[dict[str, Union["pytorjoman.Sentence", list[str]]]]:
        params = {}
        if section is not None:
            params["section"] = (
                section.id if isinstance(section, pytorjoman.Section) else section
            )
        elif project is not None:
            params["project"] = (
                project.id if isinstance(project, pytorjoman.Project) else project
            )
        status, res = await _call(
            f"{self.base_url}/api/v1/sentences/for-user",
            "GET",
            params=params,
            token=self._access_token,
        )
        match status:
            case 200:
                return [
                    {
                        "sentence": pytorjoman.Sentence(
                            self.base_url,
                            "sentences",
                            self._access_token,
                            s["id"],
                            await pytorjoman.Section.get_section(
                                self.base_url, self._access_token, s["section"]
                            ),
                            s["sentence"],
                            s["created_at"],
                        ),
                        "translations": s["translations"],
                    }
                    for s in res
                ]
            case 422:
                raise ValueError("Invalid section or project, they must be integers")
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()

    @staticmethod
    async def signup(
        base_url: str,
        first_name: str,
        last_name: str,
        email: str,
        username: str,
        password: str,
        send_time: time,
        number_of_words: int,
    ):
        status, res = await _call(
            f"{base_url}/api/v1/accounts/",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "username": username,
                "password": password,
                "send_time": send_time,
                "number_of_words": number_of_words,
            },
            with_auth=False,
        )
        match status:
            case 200:
                return Account(
                    base_url,
                    "accounts",
                    res["tokens"]["access"],
                    res["id"],
                    res["first_name"],
                    res["last_name"],
                    res["email"],
                    res["username"],
                    res["send_time"],
                    res["number_of_words"],
                    res["tokens"]["refresh"],
                )
            case 409:
                raise AlreadyExistError()
            case 422:
                raise ValueError("Incorrext values")
            case _:
                raise UnknownError()

    @staticmethod
    async def login(base_url: str, username: str, password: str):
        status, res = await _call(
            f"{base_url}/api/v1/accounts/login",
            data={"username": username, "password": password},
            with_auth=False,
        )
        match status:
            case 200:
                return Account(
                    base_url,
                    "accounts",
                    res["tokens"]["access"],
                    res["id"],
                    res["first_name"],
                    res["last_name"],
                    res["email"],
                    res["username"],
                    res["send_time"],
                    res["number_of_words"],
                    res["tokens"]["refresh"],
                )
            case 404:
                raise NotFoundError()
            case 401:
                raise IncorrectPasswordError()
            case 422:
                raise ValueError("Incorrext values")
            case _:
                raise UnknownError()

    @staticmethod
    async def login_from_token(base_url: str, access_token: str):
        status, res = await _call(
            f"{base_url}/api/v1/accounts/", "GET", token=access_token
        )
        match status:
            case 200:
                return Account(
                    base_url,
                    "accounts",
                    res["tokens"]["access"],
                    res["id"],
                    res["first_name"],
                    res["last_name"],
                    res["email"],
                    res["username"],
                    res["send_time"],
                    res["number_of_words"],
                    res["tokens"]["refresh"],
                )
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()
