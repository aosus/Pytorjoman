from typing import Optional
import httpx
from dataclasses import dataclass

async def _call(
    url: str, method: str = "POST", data: dict = {}, params: dict = {}, with_auth: bool = True, token: str=None
) -> tuple[int, dict]:
    base = {
        "url": url,
        "headers": {"Authorization": f"Bearer {token}"}
        if with_auth
        else None,
    }
    if method == "POST":
        base["json"] = data
    if params:
        base['params'] = params
    async with httpx.AsyncClient() as client:
        match method:
            case "POST":
                res = await client.post(**base)
            case "GET":
                res = await client.get(**base)
        return res.status_code, res.json()

@dataclass
class Model:
    base_url: str
    controller: str
    _access_token: str
    
    async def _call(
        self, path: str, method: str = "POST", data: dict = {}, with_auth: bool = True
    ) -> tuple[int, dict]:
        return await _call(
            f'{self.base_url}/api/v1/{self.controller}/{path}',
            method,
            data,
            with_auth,
            token=self._access_token
        )

@dataclass
class ModelList:
    count: int
    next: Optional[int]
    previous: Optional[int]
    results: list[Model]