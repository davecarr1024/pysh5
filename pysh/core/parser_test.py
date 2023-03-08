from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Sequence
from unittest import TestCase
from . import errors, lexer, parser, tokens

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    __import__('sys').modules['unittest.util']._MAX_LENGTH = 999999999


@dataclass(frozen=True)
class Val(ABC):
    @classmethod
    @abstractmethod
    def loader(cls) -> parser.SingleResultRule['Val']:
        return parser.Parser[Val](
            'val',
            parser.Scope[Val]({
                'val': parser.Or[Val]([
                    parser.Ref[Val]('int'),
                    parser.Ref[Val]('str'),
                    parser.Ref[Val]('list'),
                ]),
                'int': Int.loader(),
                'str': Str.loader(),
                'list': List.loader(),
            })
        )


@dataclass(frozen=True)
class Int(Val):
    val: int

    @staticmethod
    def _convert_token(token: tokens.Token) -> Val:
        try:
            return Int(int(token.val))
        except ValueError as error:
            raise errors.Error(msg=f'failed to load int: {error}')

    @classmethod
    def loader(cls) -> parser.SingleResultRule[Val]:
        return parser.Literal[Val](lexer.Rule.load('int', '(\\-)?(\\d)+'), Int._convert_token)


@dataclass(frozen=True)
class Str(Val):
    val: str

    @staticmethod
    def _convert_token(token: tokens.Token) -> Val:
        return Str(token.val[1:-1])

    @classmethod
    def loader(cls) -> parser.SingleResultRule[Val]:
        return parser.Literal[Val](lexer.Rule.load('str', '"(^")*"'), Str._convert_token)


@dataclass(frozen=True)
class List(Val):
    vals: Sequence[Val] = field(default_factory=list[Val])

    @classmethod
    def loader(cls) -> parser.SingleResultRule[Val]:
        return parser.combine(
            '[',
            parser.ZeroOrOne[Val](
                parser.combine(
                    parser.Ref[Val]('val'),
                    parser.ZeroOrMore[Val](
                        parser.combine(
                            ',',
                            parser.Ref[Val]('val'),
                        ).single()
                    ),
                ).convert(List)
            ).single(List()),
            ']',
        ).single()


class ScopeTest(TestCase):
    def test_or(self):
        self.assertEqual(
            parser.Scope[Val]({
                'a': Int.loader(),
            }) | parser.Scope[Val]({
                'b': Str.loader(),
            }),
            parser.Scope[Val]({
                'a': Int.loader(),
                'b': Str.loader(),
            })
        )


class ValTest(TestCase):
    def test_load(self):
        for state, expected in list[tuple[str | tokens.TokenStream, Optional[parser.StateAndResult[Val] | Val]]]([
            (
                '1',
                Int(1),
            ),
            (
                '"a"',
                Str('a'),
            ),
            (
                '[1]',
                List([Int(1)])
            ),
            (
                '[1, "a"]',
                List([Int(1), Str('a')])
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                if isinstance(state, str):
                    state = Val.loader().lexer(state)
                if expected is None:
                    with self.assertRaises(errors.Error):
                        Val.loader()(state, parser.Scope[Val]())
                else:
                    if isinstance(expected, Val):
                        expected = (tokens.TokenStream(), expected)
                    self.assertEqual(
                        Val.loader()(state, parser.Scope[Val]()),
                        expected
                    )
