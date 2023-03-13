from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence, Sized
from ..core import errors
from . import vals


@dataclass(frozen=True)
class Param:
    name: str


@dataclass(frozen=True)
class Params(Sized, Iterable[Param]):
    params: Sequence[Param]

    def __len__(self) -> int:
        return len(self.params)

    def __iter__(self) -> Iterator[Param]:
        return iter(self.params)

    def bind(self, scope: vals.Scope, args: vals.Args) -> vals.Scope:
        if len(args) != len(self):
            raise errors.Error(
                msg=f'param mismatch: expected {len(self)} args got {len(args)}')
        return scope.as_child({param.name: val.val for param, val in zip(self, args)})

    @property
    def tail(self) -> 'Params':
        if not self:
            raise errors.Error(msg='tail from empty params')
        return Params(self.params[1:])
