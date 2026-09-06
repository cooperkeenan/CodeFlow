import hashlib
import json

from fastapi import Request, Response


class ETag:
    def __init__(self, payload: object) -> None:
        body = json.dumps(payload, sort_keys=True, default=str)
        digest = hashlib.sha1(body.encode()).hexdigest()
        self._value = f'W/"{digest}"'

    def not_modified(self, request: Request) -> bool:
        return request.headers.get("if-none-match") == self._value

    def apply(self, response: Response) -> None:
        response.headers["ETag"] = self._value
