from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Iterator, MutableSequence, Optional, Sequence, Sized
from . import exprs, lex_rules, vals
from ..core import errors, lexer, parser, tokens


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

    @staticmethod
    def parser_() -> parser.Parser['Statement']:
        def load_statements(state: tokens.TokenStream, scope: parser.Scope[Statement]) -> parser.StateAndResult[Statement]:
            state, statements = parser.UntilEmpty[Statement](
                parser.Ref[Statement]('statement'))(state, scope)
            if len(statements) == 1:
                return state, statements[0]
            else:
                return state, Block(statements)

        return parser.Parser[Statement](
            'statements',
            parser.Scope[Statement]({
                'statements': load_statements,
                'statement': Statement.load,
                'block': Block.load,
                'return': Return.load,
                'assignment': Assignment.load,
                'expr_statement': ExprStatement.load,
            }),
        )

    @classmethod
    @abstractmethod
    def load(cls, state: tokens.TokenStream, scope: parser.Scope['Statement']) -> parser.StateAndResult['Statement']:
        return parser.Or[Statement]([
            parser.Ref[Statement]('block'),
            parser.Ref[Statement]('return'),
            parser.Ref[Statement]('assignment'),
            parser.Ref[Statement]('expr_statement'),
        ])(state, scope)

    @classmethod
    @abstractmethod
    def lexer_(cls) -> lexer.Lexer:
        return lex_rules.lexer_ | Block.lexer_() | Return.lexer_() | Assignment.lexer_() | ExprStatement.lexer_()


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
    def load(cls, state: tokens.TokenStream, scope: parser.Scope[Statement]) -> parser.StateAndResult[Statement]:
        state, _ = state.pop('{')
        statements: MutableSequence[Statement] = []
        while state.head().rule_name != '}':
            try:
                state, statement = parser.Ref[Statement](
                    'statement')(state, scope)
                statements.append(statement)
            except errors.Error as error:
                raise parser.StateError(state=state, children=[error])
        state, _ = state.pop('}')
        return state, Block(statements)

    @classmethod
    def lexer_(cls) -> lexer.Lexer:
        return lexer.Lexer.literals(['{', '}'])


@dataclass(frozen=True)
class ExprStatement(Statement):
    val: exprs.Expr

    def eval(self, scope: vals.Scope) -> Statement.Result:
        self.val.eval(scope)
        return Statement.Result()

    @classmethod
    def load(cls, state: tokens.TokenStream, scope: parser.Scope[Statement]) -> parser.StateAndResult[Statement]:
        state, val = exprs.Expr.parser_()(state)
        state, _ = state.pop(';')
        return state, ExprStatement(val)

    @classmethod
    def lexer_(cls) -> lexer.Lexer:
        return exprs.Expr.lexer_() | lexer.Lexer.literals([';'])


@dataclass(frozen=True)
class Assignment(Statement):
    ref: exprs.Ref
    val: exprs.Expr

    def eval(self, scope: vals.Scope) -> Statement.Result:
        self.ref.set(scope, self.val.eval(scope))
        return Statement.Result()

    @classmethod
    def load(cls, state: tokens.TokenStream, scope: parser.Scope[Statement]) -> parser.StateAndResult[Statement]:
        state, ref = exprs.Expr.parser_()(state, rule_name='ref')
        state, _ = state.pop('=')
        state, val = exprs.Expr.parser_()(state)
        state, _ = state.pop(';')
        assert isinstance(ref, exprs.Ref)
        return state, Assignment(ref, val)

    @classmethod
    def lexer_(cls) -> lexer.Lexer:
        return exprs.Expr.lexer_() | lexer.Lexer.literals([';', '='])


@dataclass(frozen=True)
class Return(Statement):
    val: Optional[exprs.Expr] = None

    def eval(self, scope: vals.Scope) -> Statement.Result:
        return Statement.Result.for_return(self.val.eval(scope) if self.val else None)

    @classmethod
    def load(cls, state: tokens.TokenStream, scope: parser.Scope[Statement]) -> parser.StateAndResult[Statement]:
        state, _ = state.pop('return')
        state, val = parser.ZeroOrOne[exprs.Expr](
            exprs.Expr.parser_())(state, exprs.Expr.parser_().scope)
        state, _ = state.pop(';')
        return state, Return(val)

    @classmethod
    def lexer_(cls) -> lexer.Lexer:
        return exprs.Expr.lexer_() | lexer.Lexer.literals([';', 'return'])
