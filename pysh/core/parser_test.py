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
                And[Val]([Val.load, Val.load]),
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
        ]):
            with self.subTest(rule=rule, state=state, scope=scope, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        rule(state, scope)
                else:
                    self.assertEqual(rule(state, scope), expected)
