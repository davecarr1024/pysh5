from abc import ABC, abstractmethod
from typing import MutableSequence
from .vals import *
from ..errors import *


class Expr(ABC):
    @abstractmethod
    def eval(self, scope: Scope) -> Val:
        ...


@dataclass(frozen=True)
class Literal(Expr):
    val: Val

    def eval(self, scope: Scope) -> Val:
        return self.val


@dataclass(frozen=True)
class Ref(Expr):
    class Head(ABC):
        @abstractmethod
        def eval(self, scope: Scope) -> Val:
            ...

        def set(self, scope: Scope, val: Val) -> None:
            raise Error(msg=f'unable to set ref head {self}')

    @dataclass(frozen=True)
    class Name(Head):
        name: str

        def eval(self, scope: Scope) -> Val:
            return scope[self.name]

        def set(self, scope: Scope, val: Val) -> None:
            scope[self.name] = val

    @dataclass(frozen=True)
    class Literal(Head):
        val: Val

        def eval(self, scope: Scope) -> Val:
            return self.val

    class Tail(ABC):
        @abstractmethod
        def eval(self, scope: Scope, val: Val) -> Val:
            ...

        def set(self, scope: Scope, obj: Val, val: Val) -> None:
            raise Error(msg=f'unable to set ref tail {self}')

    @dataclass(frozen=True)
    class Member(Tail):
        name: str

        def eval(self, scope: Scope, val: Val) -> Val:
            return val[self.name]

        def set(self, scope: Scope, obj: Val, val: Val) -> None:
            obj[self.name] = val

    @dataclass(frozen=True)
    class Call(Tail):
        args: Args

        def eval(self, scope: Scope, val: Val) -> Val:
            return val(scope, self.args)

    head: Head
    tails: Sequence[Tail] = field(default_factory=list[Tail])

    def eval(self, scope: Scope) -> Val:
        val = self.head.eval(scope)
        for tail in self.tails:
            val = tail.eval(scope, val)
        return val

    def set(self, scope: Scope, val: Val) -> None:
        if not self.tails:
            self.head.set(scope, val)
        else:
            obj = self.head.eval(scope)
            for tail in self.tails[:-1]:
                obj = tail.eval(scope, obj)
            self.tails[-1].set(scope, obj, val)


def ref(head_val: str | Val, *tail_vals: str | Args) -> Ref:
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
