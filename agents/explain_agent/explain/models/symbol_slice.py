from typing import Literal

from pydantic import BaseModel


class SymbolSlice(BaseModel):
    fqn: str
    kind: Literal["function", "class"]
    name: str
    signature: str = ""
    source: str = ""
