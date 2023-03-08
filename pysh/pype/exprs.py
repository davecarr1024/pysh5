from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Iterator, MutableSequence, Optional, Sequence, Sized, Type
from . import builtins_, classes, lex_rules, vals
from ..core import errors, lexer, parser, tokens


class Expr(ABC):
    @abstractmethod
    def eval(self, scope: vals.Scope) -> vals.Val:
        ...

    @staticmethod
    def parser_() -> parser.Parser['Expr']:
        return parser.Parser[Expr](
            'expr',
            parser.Scope[Expr]({
                'expr': Expr.load,
                'ref': Ref.load,
            }),
        )

    @classmethod
    @abstractmethod
    def load(cls, state: tokens.TokenStream, scope: parser.Scope['Expr']) -> parser.StateAndResult['Expr']:
        return parser.Or[Expr]([
            parser.Ref[Expr]('ref'),
        ])(state, scope)

    @classmethod
    @abstractmethod
    def lexer_(cls) -> lexer.Lexer:
        return lex_rules.lexer_ | Ref.lexer_()


@dataclass(frozen=True)
class Arg:
    val: Expr

    def eval(self, scope: vals.Scope) -> vals.Arg:
        return vals.Arg(self.val.eval(scope))

    @staticmethod
    def loader(scope: parser.Scope[Expr]) -> parser.SingleResultRule['Arg']:
        def inner(state: tokens.TokenStream, _: parser.Scope[Arg]) -> parser.StateAndResult[Arg]:
            state, val = Expr.load(state, scope)
            return state, Arg(val)
        return inner


@dataclass(frozen=True)
class Args(Sized, Iterable[Arg]):
    args: Sequence[Arg] = field(default_factory=list[Arg])

    def __len__(self) -> int:
        return len(self.args)

    def __iter__(self) -> Iterator[Arg]:
        return iter(self.args)

    def eval(self, scope: vals.Scope) -> vals.Args:
        return vals.Args([arg.eval(scope) for arg in self.args])

    @staticmethod
    def loader(expr_scope: parser.Scope[Expr]) -> parser.SingleResultRule['Args']:
        def inner(state: tokens.TokenStream, scope: parser.Scope[Args]) -> parser.StateAndResult[Args]:
            def load_args(state: tokens.TokenStream, scope: parser.Scope[Args]) -> parser.StateAndResult[Args]:
                load_arg = Arg.loader(expr_scope)

                def load_tail(state: tokens.TokenStream, scope: parser.Scope[Arg]) -> parser.StateAndResult[Arg]:
                    state, _ = state.pop(',')
                    return load_arg(state, scope)

                state, head = load_arg(state, parser.Scope[Arg]())
                state, tails = parser.ZeroOrMore[Arg](
                    load_tail)(state, parser.Scope[Arg]())
                return state, Args([head] + list(tails))

            state, _ = state.pop('(')
            state, args = parser.ZeroOrOne[Args](load_args)(state, scope)
            state, _ = state.pop(')')
            return state, args or Args()
        return inner

    @staticmethod
    def lexer_() -> lexer.Lexer:
        return lexer.Lexer([lex_rules.id, lex_rules.whitespace]) | lexer.Lexer.literals(['(', ',', ')'])


@dataclass(frozen=True)
class Ref(Expr):
    class Head(ABC):
        @abstractmethod
        def eval(self, scope: vals.Scope) -> vals.Val:
            ...

        def set(self, scope: vals.Scope, val: vals.Val) -> None:
            raise errors.Error(msg=f'unable to set ref head {self}')

        @classmethod
        @abstractmethod
        def load(cls, state: tokens.TokenStream, scope: parser.Scope['Ref.Head']) -> parser.StateAndResult['Ref.Head']:
            return parser.Or[Ref.Head]([Ref.Name.load, Ref.Literal.load])(state, scope)

        @classmethod
        @abstractmethod
        def lexer_(cls) -> lexer.Lexer:
            return Ref.Name.lexer_() | Ref.Literal.lexer_()

    @dataclass(frozen=True)
    class Name(Head):
        name: str

        def eval(self, scope: vals.Scope) -> vals.Val:
            return scope[self.name]

        def set(self, scope: vals.Scope, val: vals.Val) -> None:
            scope[self.name] = val

        @classmethod
        def load(cls, state: tokens.TokenStream, scope: parser.Scope['Ref.Head']) -> parser.StateAndResult['Ref.Head']:
            return parser.Literal[Ref.Head]('id', lambda token: Ref.Name(token.val))(state, scope)

        @classmethod
        def lexer_(cls) -> lexer.Lexer:
            return lexer.Lexer([lex_rules.id])

    @dataclass(frozen=True)
    class Literal(Head):
        val: vals.Val

        def eval(self, scope: vals.Scope) -> vals.Val:
            return self.val

        @classmethod
        def load(cls, state: tokens.TokenStream, scope: parser.Scope['Ref.Head']) -> parser.StateAndResult['Ref.Head']:
            state, val = builtins_.Object.parser_()(state)
            return state, Ref.Literal(val)

        @classmethod
        def lexer_(cls) -> lexer.Lexer:
            return builtins_.Object.lexer_()

    class Tail(ABC):
        @abstractmethod
        def eval(self, scope: vals.Scope, val: vals.Val) -> vals.Val:
            ...

        def set(self, scope: vals.Scope, obj: vals.Val, val: vals.Val) -> None:
            raise errors.Error(msg=f'unable to set ref tail {self}')

        @classmethod
        @abstractmethod
        def loader(cls, expr_scope: parser.Scope[Expr]) -> parser.SingleResultRule['Ref.Tail']:
            return parser.Or[Ref.Tail]([Ref.Member.loader(expr_scope), Ref.Call.loader(expr_scope)])

        @classmethod
        @abstractmethod
        def lexer_(cls) -> lexer.Lexer:
            return Ref.Member.lexer_() | Ref.Call.lexer_()

    @dataclass(frozen=True)
    class Member(Tail):
        name: str

        def eval(self, scope: vals.Scope, val: vals.Val) -> vals.Val:
            return val[self.name]

        def set(self, scope: vals.Scope, obj: vals.Val, val: vals.Val) -> None:
            obj[self.name] = val

        @classmethod
        def loader(cls, expr_scope: parser.Scope[Expr]) -> parser.SingleResultRule['Ref.Tail']:
            def load(state: tokens.TokenStream, scope: parser.Scope['Ref.Tail']) -> parser.StateAndResult['Ref.Tail']:
                state, _ = state.pop('.')
                state, name = parser.token_val(state, rule_name='id')
                return state, Ref.Member(name)
            return load

        @classmethod
        def lexer_(cls) -> lexer.Lexer:
            return lexer.Lexer([lex_rules.id]) | lexer.Lexer.literals(['.'])

    @dataclass(frozen=True)
    class Call(Tail):
        args: Args

        def eval(self, scope: vals.Scope, val: vals.Val) -> vals.Val:
            return val(scope, self.args.eval(scope))

        @classmethod
        def loader(cls, expr_scope: parser.Scope[Expr]) -> parser.SingleResultRule['Ref.Tail']:
            def load(state: tokens.TokenStream, scope: parser.Scope['Ref.Tail']) -> parser.StateAndResult['Ref.Tail']:
                state, args = Args.loader(expr_scope)(
                    state, parser.Scope[Args]())
                return state, Ref.Call(args)
            return load

        @classmethod
        def lexer_(cls) -> lexer.Lexer:
            return Args.lexer_()

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

    @classmethod
    def load(cls, state: tokens.TokenStream, scope: parser.Scope[Expr]) -> parser.StateAndResult[Expr]:
        state, head = Ref.Head.load(state, parser.Scope[Ref.Head]())
        state, tails = parser.ZeroOrMore[Ref.Tail](
            Ref.Tail.loader(scope))(state, parser.Scope[Ref.Tail]())
        return state, Ref(head, tails)

    @classmethod
    def lexer_(cls) -> lexer.Lexer:
        return Ref.Head.lexer_() | Ref.Tail.lexer_()


def ref(head_val: str | vals.Val, *tail_vals: str | Args) -> Ref:
    head: Ref.Head
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
