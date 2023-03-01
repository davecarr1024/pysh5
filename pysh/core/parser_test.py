from unittest import TestCase
from .parser import *


class Val:
    @classmethod
    @abstractmethod
    def load(cls, state: tokens.TokenStream, scope: Scope['Val']) -> StateAndResult['Val']:
        return Or[Val]([Int.load, Str.load])(state, scope)


@dataclass(frozen=True)
class Int(Val):
    val: int

    @classmethod
    def load(cls, state: tokens.TokenStream, scope: Scope[Val]) -> StateAndResult[Val]:
        try:
            return Literal[Val]('int', lambda token: Int(int(token.val)))(state, scope)
        except ValueError as error:
            raise StateError(state=state, msg=f'failed to load int: {error}')


@dataclass(frozen=True)
class Str(Val):
    val: str

    @classmethod
    def load(cls, state: tokens.TokenStream, scope: Scope[Val]) -> StateAndResult[Val]:
        return Literal[Val]('str', lambda token: Str(token.val))(state, scope)


class ScopeTest(TestCase):
    def test_or(self):
        self.assertEqual(
            Scope[Val]({
                'a': Int.load,
            }) | Scope[Val]({
                'b': Str.load,
            }),
            Scope[Val]({
                'a': Int.load,
                'b': Str.load,
            })
        )


class RuleTest(TestCase):
    def test_call(self):
        for rule, state, scope, expected in list[tuple[Rule[Val], tokens.TokenStream, Scope[Val], Optional[StateAndResult[Val]]]]([
            (
                Int.load,
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                Scope[Val](),
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
                Scope[Val](),
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
                Scope[Val](),
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
                Scope[Val](),
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
                Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('r', 'a'),
                    ]),
                    Str('a'),
                )
            ),
            (
                Ref('r'),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                Scope[Val]({
                    'r': Val.load,
                }),
                (
                    tokens.TokenStream([]),
                    Int(1),
                ),
            ),
            (
                Ref[Val]('s'),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                Scope[Val]({
                    'r': Val.load,
                }),
                None,
            ),
            (
                Parser(
                    'r',
                    Scope[Val]({
                        'r': Ref('s'),
                        's': Val.load,
                    }),
                ),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                Scope[Val](),
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
        for rule, state, scope, expected in list[tuple[MultipleResultRule[Val], tokens.TokenStream, Scope[Val], Optional[StateAndMultipleResult[Val]]]]([
            (
                And([Val.load, Val.load]),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream(),
                    [Int(1), Str('a')],
                )
            ),
            (
                And([Val.load, Val.load]),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    [Int(1), Str('a')],
                )
            ),
            (
                ZeroOrMore(Val.load),
                tokens.TokenStream([]),
                Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [],
                ),
            ),
            (
                ZeroOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                    ],
                ),
            ),
            (
                ZeroOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                        Str('a'),
                    ],
                ),
            ),
            (
                ZeroOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    [],
                ),
            ),
            (
                ZeroOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
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
                ZeroOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
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
                OneOrMore(Val.load),
                tokens.TokenStream([]),
                Scope[Val](),
                None,
            ),
            (
                OneOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                    ],
                ),
            ),
            (
                OneOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                        Str('a'),
                    ],
                ),
            ),
            (
                OneOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
                None,
            ),
            (
                OneOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
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
                OneOrMore(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
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
                UntilEmpty(Val.load),
                tokens.TokenStream([]),
                Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [],
                ),
            ),
            (
                UntilEmpty(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                    ],
                ),
            ),
            (
                UntilEmpty(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream([]),
                    [
                        Int(1),
                        Str('a'),
                    ],
                ),
            ),
            (
                UntilEmpty(Val.load),
                tokens.TokenStream([
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
                None,
            ),
            (
                UntilEmpty(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
                None,
            ),
            (
                UntilEmpty(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('str', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
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
        for rule, state, scope, expected in list[tuple[OptionalResultRule[Val], tokens.TokenStream, Scope[Val], Optional[StateAndOptionalResult[Val]]]]([
            (
                ZeroOrOne(Val.load),
                tokens.TokenStream([]),
                Scope[Val](),
                (
                    tokens.TokenStream([]),
                    None,
                ),
            ),
            (
                ZeroOrOne(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream([]),
                    Int(1),
                ),
            ),
            (
                ZeroOrOne(Val.load),
                tokens.TokenStream([
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    None,
                ),
            ),
            (
                ZeroOrOne(Val.load),
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('s', 'b'),
                ]),
                Scope[Val](),
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
