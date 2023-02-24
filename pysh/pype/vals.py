from dataclasses import field
from typing import Iterable, Iterator, Mapping, MutableMapping, Sequence, Sized
from ..errors import *


class Val(MutableMapping[str, 'Val']):
    def __call__(self, scope: 'Scope', args: 'Args') -> 'Val':
        raise Error(msg=f'calling uncallable val {self}')

    def __len__(self) -> int:
        return len(self.members)

    def __iter__(self) -> Iterator[str]:
        return iter(self.members)

    def __getitem__(self, name: str) -> 'Val':
        return self.members[name]

    def __setitem__(self, name: str, val: 'Val') -> None:
        self.members[name] = val

    def __delitem__(self, name: str) -> None:
        del self.members[name]

    def __contains__(self, name: object) -> bool:
        return name in self.members

    @property
    def members(self) -> 'Scope':
        return Scope()

    @property
    def can_bind(self) -> bool:
        return False

    def bind(self, object_: 'Val') -> 'Val':
        raise Error(msg=f'binding unbindable val {self}')


@dataclass(frozen=True)
class Scope(MutableMapping[str, Val]):
    _vals: MutableMapping[str, Val] = field(default_factory=dict[str, Val])
    parent: Optional['Scope'] = field(kw_only=True, default=None)

    def __getitem__(self, name: str) -> Val:
        if name in self._vals:
            return self._vals[name]
        elif self.parent is not None:
            return self.parent[name]
        else:
            raise Error(msg=f'unknown var {name}')

    def __setitem__(self, name: str, val: Val) -> None:
        self._vals[name] = val

    def __delitem__(self, name: str) -> None:
        if name in self._vals:
            del self._vals[name]
        else:
            raise Error(msg=f'del unknown var {name}')

    def __len__(self) -> int:
        return len(self.all_vals)

    def __iter__(self) -> Iterator[str]:
        return iter(self.all_vals)

    def __contains__(self, name: object) -> bool:
        return name in self._vals or (self.parent is not None and name in self.parent)

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, Scope) and rhs.all_vals == self.all_vals

    def as_child(self, vals: Optional[MutableMapping[str, Val]] = None) -> 'Scope':
        return Scope(parent=self, _vals=vals or {})

    @property
    def all_vals(self) -> Mapping[str, Val]:
        vals: MutableMapping[str, Val] = {}
        if self.parent is not None:
            vals |= self.parent.all_vals
        vals |= self._vals
        return vals

    def bind(self, object_: Val) -> None:
        for name, val in self.all_vals.items():
            if val.can_bind:
                self[name] = val.bind(object_)


@dataclass(frozen=True)
class Arg:
    val: Val


@dataclass(frozen=True)
class Args(Sized, Iterable[Arg]):
    args: Sequence[Arg]

    def __len__(self) -> int:
        return len(self.args)

    def __iter__(self) -> Iterator[Arg]:
        return iter(self.args)

    def prepend(self, arg: Arg) -> 'Args':
        return Args([arg]+list(self.args))


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

    def bind(self, scope: Scope, args: Args) -> Scope:
        if len(args) != len(self):
            raise Error(
                msg=f'param mismatch: expected {len(self)} args got {len(args)}')
        return scope.as_child({param.name: val.val for param, val in zip(self, args)})

    @property
    def tail(self) -> 'Params':
        if not self:
            raise Error(msg='tail from empty params')
        return Params(self.params[1:])
