from dataclasses import dataclass, field
from typing import Optional, Sequence


@dataclass(frozen=True, kw_only=True)
class Error(Exception):
    msg: Optional[str] = None

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return f'Error(msg={self.msg})'


@dataclass(frozen=True, kw_only=True)
class NaryError(Error):
    children: Sequence[Error] = field(default_factory=list[Error])

    def _repr(self) -> str:
        return repr(self.msg)

    def __repr(self, indent: int) -> str:
        return f"{'  '*indent}{self._repr()}"
        return f"{'  '*indent}{self.__repr(0)}\n"

    def __repr__(self) -> str:
        return self.__repr(0)
