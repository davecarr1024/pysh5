from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from unittest import TestCase
from . import errors, lexer, parser, tokens


@dataclass(frozen=True)
class Val(ABC):
    @classmethod
    @abstractmethod
    def load(cls, state: tokens.TokenStream, scope: parser.Scope['Val']) -> parser.StateAndResult['Val']:
        return parser.Or[Val]([Int.load, Str.load])(state, scope)


@dataclass(frozen=True)
class Int(Val):
    val: int

    @classmethod
    def load(cls, state: tokens.TokenStream, scope: parser.Scope[Val]) -> parser.StateAndResult[Val]:
        try:
            return parser.Literal[Val]('int', lambda token: Int(int(token.val)))(state, scope)
        except ValueError as error:
            raise parser.StateError(
                state=state, msg=f'failed to load int: {error}')


@dataclass(frozen=True)
class Str(Val):
    val: str

    @classmethod
    def load(cls, state: tokens.TokenStream, scope: parser.Scope[Val]) -> parser.StateAndResult[Val]:
        return parser.Literal[Val]('str', lambda token: Str(token.val))(state, scope)


class ScopeTest(TestCase):
    def test_or(self):
        self.assertEqual(
            parser.Scope[Val]({
                'a': Int.load,
            }) | parser.Scope[Val]({
                'b': Str.load,
            }),
            parser.Scope[Val]({
                'a': Int.load,
                'b': Str.load,
            })
        )


class RuleTest(TestCase):
    def test_call(self):
        for rule, state, scope, expected in list[tuple[parser.Rule[Val], tokens.TokenStream, parser.Scope[Val], Optional[parser.StateAndResult[Val]]]]([
            (
                Int.load,
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream(),
                    Int(1),
                )
            ),
            (
                Int.load,
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('r', 'a'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('r', 'a'),
                    ]),
                    Int(1),
                )
            ),
            (
                Val.load,
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream(),
                    Int(1),
                )
            ),
            (
                Val.load,
                tokens.TokenStream([
                    tokens.Token('str', 'a'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream(),
                    Str('a'),
                )
            ),
            (
                Val.load,
                tokens.TokenStream([
                    tokens.Token('str', 'a'),
                    tokens.Token('r', 'a'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('r', 'a'),
                    ]),
                    Str('a'),
                )
            ),
            (
                parser.Ref('r'),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                parser.Scope[Val]({
                    'r': Val.load,
                }),
                (
                    tokens.TokenStream([]),
                    Int(1),
                ),
            ),
            (
                parser.Ref[Val]('s'),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                parser.Scope[Val]({
                    'r': Val.load,
                }),
                None,
            ),
            (
                parser.Parser(
                    'r',
                    parser.Scope[Val]({
                        'r': parser.Ref('s'),
                        's': Val.load,
                    }),
                ),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    Int(1),
                ),
            ),
        ]):
            with self.subTest(rule=rule, state=state, scope=scope, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        rule(state, scope)
                else:
                    self.assertEqual(rule(state, scope), expected)

    def test_call_multiple_result(self):
        for rule, state, scope, expected in list[tuple[parser.MultipleResultRule[Val], tokens.TokenStream, parser.Scope[Val], Optional[parser.StateAndMultipleResult[Val]]]]([
            (
                parser.And([Val.load, Val.load]),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream(),
                    [Int(1), Str('a')],
                )
            ),
            (
                parser.And([Val.load, Val.load]),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    [Int(1), Str('a')],
                )
            ),
            (
                parser.ZeroOrMore(Val.load),
                tokens.TokenStream([]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [],
                ),
            ),
            (
                parser.ZeroOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                    ],
                ),
            ),
            (
                parser.ZeroOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                        Str('a'),
                    ],
                ),
            ),
            (
                parser.ZeroOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    [],
                ),
            ),
            (
                parser.ZeroOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    [
                        Int(1),
                    ],
                ),
            ),
            (
                parser.ZeroOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    [
                        Int(1),
                        Str('a'),
                    ],
                ),
            ),
            (
                parser.OneOrMore(Val.load),
                tokens.TokenStream([]),
                parser.Scope[Val](),
                None,
            ),
            (
                parser.OneOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                    ],
                ),
            ),
            (
                parser.OneOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                        Str('a'),
                    ],
                ),
            ),
            (
                parser.OneOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                None,
            ),
            (
                parser.OneOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    [
                        Int(1),
                    ],
                ),
            ),
            (
                parser.OneOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    [
                        Int(1),
                        Str('a'),
                    ],
                ),
            ),
            (
                parser.UntilEmpty(Val.load),
                tokens.TokenStream([]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [],
                ),
            ),
            (
                parser.UntilEmpty(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                    ],
                ),
            ),
            (
                parser.UntilEmpty(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                        Str('a'),
                    ],
                ),
            ),
            (
                parser.UntilEmpty(Val.load),
                tokens.TokenStream([
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                None,
            ),
            (
                parser.UntilEmpty(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                None,
            ),
            (
                parser.UntilEmpty(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                None,
            ),
        ]):
            with self.subTest(rule=rule, state=state, scope=scope, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        rule(state, scope)
                else:
                    self.assertEqual(rule(state, scope), expected)

    def test_call_optional(self):
        for rule, state, scope, expected in list[tuple[parser.OptionalResultRule[Val], tokens.TokenStream, parser.Scope[Val], Optional[parser.StateAndOptionalResult[Val]]]]([
            (
                parser.ZeroOrOne(Val.load),
                tokens.TokenStream([]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    None,
                ),
            ),
            (
                parser.ZeroOrOne(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([]),
                    Int(1),
                ),
            ),
            (
                parser.ZeroOrOne(Val.load),
                tokens.TokenStream([
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    None,
                ),
            ),
            (
                parser.ZeroOrOne(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('s', 'b'),
                ]),
                parser.Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    Int(1),
                ),
            ),
        ]):
            with self.subTest(rule=rule, state=state, scope=scope, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        rule(state, scope)
                else:
                    self.assertEqual(rule(state, scope), expected)

    def test_token_val(self):
        for state, rule_name, expected in list[tuple[tokens.TokenStream, Optional[str], Optional[parser.StateAndResult[str]]]]([
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
                None,
                (
                    tokens.TokenStream([]),
                    'a',
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                None,
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    'a',
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
                'r',
                (
                    tokens.TokenStream([]),
                    'a',
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                'r',
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    'a',
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
                's',
                None,
            ),
            (
                tokens.TokenStream([
                ]),
                None,
                None,
            ),
        ]):
            with self.subTest(state=state, rule_name=rule_name, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        parser.token_val(state, rule_name=rule_name)
                else:
                    self.assertEqual(
                        parser.token_val(state, rule_name=rule_name), expected)
