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
                'val': (
                    parser.Ref[Val]('int')
                    | parser.Ref[Val]('str')
                    | parser.Ref[Val]('list')
                ),
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
        return (
            '['
            & (
                parser.Ref[Val]('val')
                & (
                    ','
                    & parser.Ref[Val]('val')
                ).single().zero_or_more()
            ).convert(List).zero_or_one().single(List())
            & ']'
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
                '[1,"a"]',
                List([Int(1), Str('a')])
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                if isinstance(state, str):
                    state = Val.loader().lexer_(state)
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


class ParserTest(TestCase):
    def test_apply(self):
        for rule, state, scope, expected in list[tuple[parser.SingleResultRule[Val], tokens.TokenStream, parser.Scope[Val], Optional[parser.StateAndResult[Val]]]]([
            (
                parser.Ref[Val]('int'),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                parser.Scope[Val]({
                    'int': Int.loader(),
                }),
                (
                    tokens.TokenStream([]),
                    Int(1),
                ),
            ),
            (
                parser.Literal[Val](
                    lexer.Rule.load('a'),
                    lambda _: Int(1),
                ),
                tokens.TokenStream([
                    tokens.Token('a', 'a'),
                ]),
                parser.Scope({}),
                (
                    tokens.TokenStream([]),
                    Int(1),
                ),
            ),
            (
                (Int.loader() & Int.loader()).convert(List),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('int', '2'),
                ]),
                parser.Scope({}),
                (
                    tokens.TokenStream([]),
                    List([Int(1), Int(2)]),
                )
            )
        ]):
            with self.subTest(rule=rule, state=state, scope=scope, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        rule(state, scope)
                else:
                    self.assertEqual(rule(state, scope), expected)
