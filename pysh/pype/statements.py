from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional, Sequence, Sized, Type
from . import exprs,  vals
from ..core import errors, lexer, parser, tokens


class Statement(parser.Parsable['Statement']):
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

    @classmethod
    def types(cls) -> Sequence[Type['Statement']]:
        from . import func
        return [
            Return,
            Block,
            ExprStatement,
            Assignment,
            func.Decl,
        ]


@dataclass(frozen=True)
class Block(Statement, Sized, Iterable[Statement]):
    statements: Sequence[Statement] = field(default_factory=list[Statement])

    def __len__(self) -> int:
        return len(self.statements)

    def __iter__(self) -> Iterator[Statement]:
        return iter(self.statements)

    def eval(self, scope: vals.Scope) -> Statement.Result:
        scope = vals.Scope(parent=scope)
        for statement in self.statements:
            result = statement.eval(scope)
            if result.is_return():
                return result
        return Statement.Result()

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Statement]:
        close_brace_lex_rule = lexer.Rule.load('}')
        return (
            '{' &
            Statement.ref().until_token(close_brace_lex_rule) &
            close_brace_lex_rule
        ).convert(Block).with_lexer(lexer.Lexer.whitespace())


@dataclass(frozen=True)
class ExprStatement(Statement):
    val: exprs.Expr

    def eval(self, scope: vals.Scope) -> Statement.Result:
        self.val.eval(scope)
        return Statement.Result()

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Statement]:
        def load(val: exprs.Expr) -> Statement:
            return ExprStatement(val)
        return (exprs.Expr.parser_().convert_type(load) & ';').with_lexer(lexer.Lexer.whitespace())


@dataclass(frozen=True)
class Assignment(Statement):
    name: exprs.Ref
    val: exprs.Expr

    def eval(self, scope: vals.Scope) -> Statement.Result:
        self.name.set(scope, self.val.eval(scope))
        return Statement.Result()

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Statement]:
        class Adapter(parser.SingleResultRule[Statement]):
            def __call__(self, state: tokens.TokenStream, scope: parser.Scope[Statement]) -> parser.StateAndSingleResult[Statement]:
                state, name = exprs.Ref._parse_rule()(state, exprs.Expr.parser_().scope)
                assert isinstance(name, exprs.Ref)
                state, _ = state.pop('=')
                state, val = exprs.Expr.parser_()(state)
                state, _ = state.pop(';')
                return state, Assignment(name, val)

            @property
            def lexer_(self) -> lexer.Lexer:
                return lexer.Lexer.literal('=', ';') | exprs.Expr.parser_().lexer_ | lexer.Lexer.whitespace()

        return Adapter()


@dataclass(frozen=True)
class Return(Statement):
    val: Optional[exprs.Expr] = None

    def eval(self, scope: vals.Scope) -> Statement.Result:
        return Statement.Result.for_return(self.val.eval(scope) if self.val else None)

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Statement]:
        def load(val: Optional[exprs.Expr]) -> Statement:
            return Return(val)
        return (
            'return' &
            exprs.Expr.parser_().zero_or_one() &
            ';'
        ).convert_type(load).with_lexer(lexer.Lexer.whitespace())


@dataclass(frozen=True)
class AbstractDecl(Statement):
    name: str

    @property
    @abstractmethod
    def val(self) -> exprs.Expr:
        ...

    def eval(self, scope: vals.Scope) -> Statement.Result:
        scope[self.name] = self.val.eval(scope)
        return Statement.Result()
