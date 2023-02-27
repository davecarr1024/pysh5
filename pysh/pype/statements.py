from .exprs import *


class Statement(ABC):
    @dataclass(frozen=True)
    class Result:
        @dataclass(frozen=True)
        class Return:
            val: Optional[Val] = None

            def has_value(self) -> bool:
                return self.val is not None

        return_: Optional[Return] = None

        def is_return(self) -> bool:
            return self.return_ is not None

        def has_return_value(self) -> bool:
            return self.return_ is not None and self.return_.has_value()

        def return_value(self) -> Val:
            if not self.has_return_value():
                raise Error(
                    msg=f'getting return value from incompatible result {self}')
            assert self.return_ and self.return_.val
            return self.return_.val

        @staticmethod
        def for_return(val: Optional[Val] = None) -> 'Statement.Result':
            return Statement.Result(Statement.Result.Return(val))

    @abstractmethod
    def eval(self, scope: Scope) -> Result:
        ...


@dataclass(frozen=True)
class Block(Statement):
    statements: Sequence[Statement]

    def eval(self, scope: Scope) -> Statement.Result:
        for statement in self.statements:
            result = statement.eval(scope)
            if result.is_return():
                return result
        return Statement.Result()


@dataclass(frozen=True)
class ExprStatement(Statement):
    val: Expr

    def eval(self, scope: Scope) -> Statement.Result:
        self.val.eval(scope)
        return Statement.Result()


@dataclass(frozen=True)
class Assignment(Statement):
    ref: Ref
    val: Expr

    def eval(self, scope: Scope) -> Statement.Result:
        self.ref.set(scope, self.val.eval(scope))
        return Statement.Result()


@dataclass(frozen=True)
class Return(Statement):
    val: Optional[Expr] = None

    def eval(self, scope: Scope) -> Statement.Result:
        return Statement.Result.for_return(self.val.eval(scope) if self.val else None)
