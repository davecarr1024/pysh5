from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import MutableSequence, Sequence, Type
from . import vals
from ..core import errors


class Expr(ABC):
    @abstractmethod
    def eval(self, scope: vals.Scope) -> vals.Val:
        ...

    @classmethod
    def types(cls) -> Sequence[Type['Expr']]:
        return [
            Expr,
            Literal,
            Ref,
        ]


@dataclass(frozen=True)
class Literal(Expr):
    val: vals.Val

    def eval(self, scope: vals.Scope) -> vals.Val:
        return self.val


@dataclass(frozen=True)
class Ref(Expr):
    class Head(ABC):
        @abstractmethod
        def eval(self, scope: vals.Scope) -> vals.Val:
            ...

        def set(self, scope: vals.Scope, val: vals.Val) -> None:
            raise errors.Error(msg=f'unable to set ref head {self}')

    @dataclass(frozen=True)
    class Name(Head):
        name: str

        def eval(self, scope: vals.Scope) -> vals.Val:
            return scope[self.name]

        def set(self, scope: vals.Scope, val: vals.Val) -> None:
            scope[self.name] = val

    @dataclass(frozen=True)
    class Literal(Head):
        val: vals.Val

        def eval(self, scope: vals.Scope) -> vals.Val:
            return self.val

    class Tail(ABC):
        @abstractmethod
        def eval(self, scope: vals.Scope, val: vals.Val) -> vals.Val:
            ...

        def set(self, scope: vals.Scope, obj: vals.Val, val: vals.Val) -> None:
            raise errors.Error(msg=f'unable to set ref tail {self}')

    @dataclass(frozen=True)
    class Member(Tail):
        name: str

        def eval(self, scope: vals.Scope, val: vals.Val) -> vals.Val:
            return val[self.name]

        def set(self, scope: vals.Scope, obj: vals.Val, val: vals.Val) -> None:
            obj[self.name] = val

    @dataclass(frozen=True)
    class Call(Tail):
        args: vals.Args

        def eval(self, scope: vals.Scope, val: vals.Val) -> vals.Val:
            return val(scope, self.args)

    head: Head
    tails: Sequence[Tail] = field(default_factory=list[Tail])

    def eval(self, scope: vals.Scope) -> vals.Val:
        val = self.head.eval(scope)
        for tail in self.tails:
            val = tail.eval(scope, val)
        return val

    def set(self, scope: vals.Scope, val: vals.Val) -> None:
        if not self.tails:
            self.head.set(scope, val)
        else:
            obj = self.head.eval(scope)
            for tail in self.tails[:-1]:
                obj = tail.eval(scope, obj)
            self.tails[-1].set(scope, obj, val)


def ref(head_val: str | vals.Val, *tail_vals: str | vals.Args) -> Ref:
    if isinstance(head_val, str):
        head = Ref.Name(head_val)
    else:
        head = Ref.Literal(head_val)
    tails: MutableSequence[Ref.Tail] = []
    for tail_val in tail_vals:
        if isinstance(tail_val, str):
            tails.append(Ref.Member(tail_val))
        else:
            tails.append(Ref.Call(tail_val))
    return Ref(head, tails)
