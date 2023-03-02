from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional, Sequence, Sized
from . import exprs, vals
from ..core import errors


class Statement(ABC):
    @dataclass(frozen=True)
    class Result:
        @dataclass(frozen=True)
        class Return:
            val: Optional[vals.Val] = None

            def has_value(self) -> bool:
                return self.val is not None

        return_: Optional[Return] = None

        def is_return(self) -> bool:
            return self.return_ is not None

        def has_return_value(self) -> bool:
            return self.return_ is not None and self.return_.has_value()

        def return_value(self) -> vals.Val:
            if not self.has_return_value():
                raise errors.Error(
                    msg=f'getting return value from incompatible result {self}')
            assert self.return_ and self.return_.val
            return self.return_.val

        @staticmethod
        def for_return(val: Optional[vals.Val] = None) -> 'Statement.Result':
            return Statement.Result(Statement.Result.Return(val))

    @abstractmethod
    def eval(self, scope: vals.Scope) -> Result:
        ...


@dataclass(frozen=True)
class Block(Statement, Sized, Iterable[Statement]):
    statements: Sequence[Statement]

    def __len__(self) -> int:
        return len(self.statements)

    def __iter__(self) -> Iterator[Statement]:
        return iter(self.statements)

    def eval(self, scope: vals.Scope) -> Statement.Result:
        for statement in self.statements:
            result = statement.eval(scope)
            if result.is_return():
                return result
        return Statement.Result()


@dataclass(frozen=True)
class ExprStatement(Statement):
    val: exprs.Expr

    def eval(self, scope: vals.Scope) -> Statement.Result:
        self.val.eval(scope)
        return Statement.Result()


@dataclass(frozen=True)
class Assignment(Statement):
    ref: exprs.Ref
    val: exprs.Expr

    def eval(self, scope: vals.Scope) -> Statement.Result:
        self.ref.set(scope, self.val.eval(scope))
        return Statement.Result()


@dataclass(frozen=True)
class Return(Statement):
    val: Optional[exprs.Expr] = None

    def eval(self, scope: vals.Scope) -> Statement.Result:
        return Statement.Result.for_return(self.val.eval(scope) if self.val else None)
