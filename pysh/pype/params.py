from dataclasses import dataclass, field
from typing import Iterable, Iterator, Sequence, Sized
from ..core import errors, lexer, parser
from . import exprs, vals


@dataclass(frozen=True)
class Param:
    name: str

    @staticmethod
    def parse_rule() -> parser.SingleResultRule['Param']:
        return parser.Literal(exprs.id_lex_rule, lambda token: Param(token.val))


@dataclass(frozen=True)
class Params(Sized, Iterable[Param]):
    params: Sequence[Param] = field(default_factory=list[Param])

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

    @staticmethod
    def parse_rule() -> parser.SingleResultRule['Params']:
        return (
            '(' &
            (
                Param.parse_rule() &
                (
                    ',' &
                    Param.parse_rule()
                ).zero_or_more()
            ).convert_type(Params).zero_or_one().single_or(Params())
            & ')'
        ).with_lexer(lexer.Lexer.whitespace())
