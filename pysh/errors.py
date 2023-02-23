from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class Error(Exception):
    msg: Optional[str] = None
