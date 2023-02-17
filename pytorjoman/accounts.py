from dataclasses import dataclass
from datetime import time
from pytorjoman._backend import Model, _call
from pytorjoman.errors import AlreadyExistError, NotFoundError, IncorrectPasswordError, TokenExpiredError, UnknownError, UnloggedInError

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
    
    async def update(self, first_name: str | None = None, last_name: str | None = None, send_time: time | None = None, number_of_words: int | None = None) -> None:
        data = {}
        if first_name:
            data['first_name'] = first_name
        if last_name:
            data['last_name'] = last_name
        if send_time:
            data['send_time'] = send_time
        if number_of_words:
            data['number_of_words'] = number_of_words
        status, res = await self._call('update', data=data)
        match status:
            case 200:
                self.id = res['id']
                self.first_name = res['first_name']
                self.last_name = res['last_name']
                self.email = res['email']
                self.username = res['username']
                self.send_time = res['send_time']
                self.number_of_words = res['number_of_words']
                self._access_token = res['tokens']['access']
                self._refresh_token = res['tokens']['refresh']
            case 401:
                raise TokenExpiredError()
            case _:
                raise UnknownError()
    
    async def refresh_token(self):
        status, res = await self._call(
            f'refresh/{self._refresh_token}',
            "GET",
            with_auth=False
        )
        match status:
            case 200:
                self._access_token = res['access']
                self._refresh_token = res['refresh']
            case 401:
                raise TokenExpiredError()
            case _:
                return UnknownError()

    async def change_password(self, current_password: str, new_password: str):
        status, res = await self._call(
            f'change-password',
            data={
                'current_password': current_password,
                'new_password': new_password
            }
        )
        match status:
            case 200:
                self._access_token = res['access']
                self._refresh_token = res['refresh']
            case 401:
                match res['detail']:
                    case 'incorrect_password':
                        raise IncorrectPasswordError()
                    case 'Unauthorized':
                        raise TokenExpiredError()
            case 422:
                raise ValueError("password lenght must be between 8 and 50")
            case _:
                return UnknownError()
    
    @staticmethod
    async def signup(base_url: str, first_name: str, last_name: str, email: str, username: str, password: str, send_time: time, number_of_words: int):
        status, res = await _call(
            f'{base_url}/api/v1/accounts/',
            data={
                'frist_name': first_name,
                'last_name': last_name,
                'email': email,
                'username': username,
                'password': password,
                'send_time': send_time,
                'number_of_words': number_of_words
            },
            with_auth=False
        )
        match status:
            case 200:
                return Account(
                    base_url,
                    'accounts',
                    res['tokens']['access'],
                    res['id'],
                    res['first_name'],
                    res['last_name'],
                    res['email'],
                    res['username'],
                    res['send_time'],
                    res['number_of_words'],
                    res['tokens']['refresh'],
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
            f'{base_url}/api/v1/accounts/login',
            data={
                'username': username,
                'password': password
            },
            with_auth=False
        )
        match status:
            case 200:
                return Account(
                    base_url,
                    'accounts',
                    res['tokens']['access'],
                    res['id'],
                    res['first_name'],
                    res['last_name'],
                    res['email'],
                    res['username'],
                    res['send_time'],
                    res['number_of_words'],
                    res['tokens']['refresh']
                )
            case 404:
                raise NotFoundError()
            case 401:
                raise IncorrectPasswordError()
            case 422:
                raise ValueError("Incorrext values")
            case _:
                raise UnknownError()