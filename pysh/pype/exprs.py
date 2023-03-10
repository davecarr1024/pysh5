from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Iterator, MutableSequence, Sequence, Sized, Type
from . import builtins_, vals
from ..core import errors, lexer, parser, tokens


class Expr(parser.Parsable['Expr']):
    @abstractmethod
    def eval(self, scope: vals.Scope) -> vals.Val:
        ...

    @classmethod
    def types(cls) -> Sequence[Type['Expr']]:
        return [
            Ref,
        ]


@dataclass(frozen=True)
class Arg:
    val: Expr

    def eval(self, scope: vals.Scope) -> vals.Arg:
        return vals.Arg(self.val.eval(scope))

    @staticmethod
    def parse_rule() -> parser.SingleResultRule['Arg']:
        return Expr.parser_().convert_type(Arg).without_lexer()


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
    def parse_rule() -> parser.SingleResultRule['Args']:
        return (
            '(' &
            (
                Arg.parse_rule() &
                (
                    ',' &
                    Arg.parse_rule()
                ).zero_or_more()
            ).convert_type(Args).zero_or_one().single_or(Args()) &
            ')'
        ).with_lexer(lexer.Lexer.whitespace())


_id_lex_rule = lexer.Rule.load('id', '(_|[a-z]|[A-Z])+')


@dataclass(frozen=True)
class Ref(Expr):
    class Head(parser.Parsable['Ref.Head']):
        @abstractmethod
        def eval(self, scope: vals.Scope) -> vals.Val:
            ...

        def set(self, scope: vals.Scope, val: vals.Val) -> None:
            raise errors.Error(msg=f'unable to set ref head {self}')

        @classmethod
        def types(cls) -> Sequence[Type['Ref.Head']]:
            return [
                Ref.Name,
                Ref.Literal,
            ]

    @dataclass(frozen=True)
    class Name(Head):
        name: str

        def eval(self, scope: vals.Scope) -> vals.Val:
            return scope[self.name]

        def set(self, scope: vals.Scope, val: vals.Val) -> None:
            scope[self.name] = val

        @classmethod
        def _parse_rule(cls) -> parser.SingleResultRule['Ref.Head']:
            return parser.Literal(
                _id_lex_rule,
                lambda token: Ref.Name(token.val),
            )

    @dataclass(frozen=True)
    class Literal(Head):
        val: vals.Val

        def eval(self, scope: vals.Scope) -> vals.Val:
            return self.val

        @classmethod
        def _parse_rule(cls) -> parser.SingleResultRule['Ref.Head']:
            return builtins_.Object.parser_().convert_type(Ref.Literal)

    class Tail(parser.Parsable['Ref.Tail']):
        @abstractmethod
        def eval(self, scope: vals.Scope, val: vals.Val) -> vals.Val:
            ...

        def set(self, scope: vals.Scope, obj: vals.Val, val: vals.Val) -> None:
            raise errors.Error(msg=f'unable to set ref tail {self}')

        @classmethod
        def types(cls) -> Sequence[Type['Ref.Tail']]:
            return [
                Ref.Member,
                Ref.Call,
            ]

    @dataclass(frozen=True)
    class Member(Tail):
        name: str

        def eval(self, scope: vals.Scope, val: vals.Val) -> vals.Val:
            return val[self.name]

        def set(self, scope: vals.Scope, obj: vals.Val, val: vals.Val) -> None:
            obj[self.name] = val

        @classmethod
        def _parse_rule(cls) -> parser.SingleResultRule['Ref.Tail']:
            return '.' & parser.Literal[Ref.Tail](_id_lex_rule, lambda token: Ref.Member(token.val))

    @dataclass(frozen=True)
    class Call(Tail):
        args: Args

        def eval(self, scope: vals.Scope, val: vals.Val) -> vals.Val:
            return val(scope, self.args.eval(scope))

        @classmethod
        def _parse_rule(cls) -> parser.SingleResultRule['Ref.Tail']:
            return Args.parse_rule().convert_type(Ref.Call)

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
    def _parse_rule(cls) -> parser.SingleResultRule[Expr]:
        class Adapter(parser.SingleResultRule[Expr]):
            def __call__(self, state: tokens.TokenStream, scope: parser.Scope[Expr]) -> parser.StateAndSingleResult[Expr]:
                state, head = Ref.Head.parser_()(state)
                state, tails = Ref.Tail.parser_().zero_or_more()(state, Ref.Tail.parser_().scope)
                return state, Ref(head, tails)

            @property
            def lexer_(self) -> lexer.Lexer:
                return Ref.Head.parser_().lexer_ | Ref.Tail.parser_().lexer_

        return Adapter()


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
