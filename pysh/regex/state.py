from dataclasses import dataclass, field
from .errors import *


@dataclass(frozen=True)
class Char:
    val: str

    def __str__(self) -> str:
        return self.val

    def __post_init__(self):
        if len(self.val) != 1:
            raise Error(msg=f'invalid char {self}')


@dataclass(frozen=True)
class State:
    _vals: list[Char] = field(default_factory=list[Char])

    def __bool__(self) -> bool:
        return bool(self._vals)

    def head(self) -> Char:
        if not self:
            raise Error(msg='head of empty state')
        return self._vals[0]

    def tail(self) -> 'State':
        if not self:
            raise Error(msg='tail of empty state')
        return State(self._vals[1:])

    @staticmethod
    def load(s: str):
        return State([Char(c) for c in s])


@dataclass(frozen=True)
class Result:
    val: str = ''

    def __add__(self, rhs: 'Result') -> 'Result':
        return Result(self.val + rhs.val)


StateAndResult = tuple[State, Result]
