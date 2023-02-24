from unittest import TestCase
from .rules import *


class Val:
    @classmethod
    @abstractmethod
    def load(cls, scope: Scope['Val'], state: TokenStream) -> StateAndResult['Val']:
        return Or([Int.load, Str.load])(scope, state)


@dataclass(frozen=True)
class Int(Val):
    val: int

    @classmethod
    def load(cls, scope: Scope[Val], state: TokenStream) -> StateAndResult['Val']:
        try:
            return Literal[Val]('int', lambda token: Int(int(token.val)))(scope, state)
        except ValueError as error:
            raise StateError(state=state, children=[],
                             msg=f'invalid value: {error}')


@dataclass(frozen=True)
class Str(Val):
    val: str

    @classmethod
    def load(cls, scope: Scope[Val], state: TokenStream) -> StateAndResult['Val']:
        return Literal[Val]('str', lambda token: Str(token.val))(scope, state)


class LiteralTest(TestCase):
    def test_load(self):
        for state, expected in list[tuple[TokenStream, StateAndResult[Int]]]([
            (
                TokenStream([Token('int', '1')]),
                (TokenStream(), Int(1)),
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('int', '2'),
                ]),
                (TokenStream([Token('int', '2')]), Int(1)),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(Int.load(Scope[Val](), state), expected)

    def test_load_fail(self):
        for state in list[TokenStream]([
            TokenStream(),
            TokenStream([Token('float', '3.14')]),
            TokenStream([Token('int', 'abc')]),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    Int.load(Scope[Val](), state)


class RefTest(TestCase):
    def test_load(self):
        for state, expected in list[tuple[TokenStream, StateAndResult[Int]]]([
            (
                TokenStream([Token('int', '1')]),
                (TokenStream(), Int(1)),
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('int', '2'),
                ]),
                (TokenStream([Token('int', '2')]), Int(1)),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    Ref('a')(
                        Scope[Val]({
                            'a': Int.load,
                        }),
                        state,
                    ), expected)

    def test_load_fail(self):
        for state in list[TokenStream]([
            TokenStream(),
            TokenStream([Token('float', '3.14')]),
            TokenStream([Token('int', 'abc')]),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    Ref('a')(
                        Scope[Val]({
                            'a': Int.load,
                        }),
                        state,
                    )


class AndTest(TestCase):
    def test_call(self):
        for state, expected in list[tuple[TokenStream, StateAndMultipleResult[Int]]]([
            (
                TokenStream([
                    Token('int', '1'),
                    Token('int', '2'),
                ]),
                (
                    TokenStream(),
                    [
                        Int(1),
                        Int(2),
                    ]
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('int', '2'),
                    Token('int', '3'),
                ]),
                (
                    TokenStream([Token('int', '3')]),
                    [
                        Int(1),
                        Int(2),
                    ]
                )
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    And([Int.load, Int.load])(Scope[Val](), state),
                    expected
                )

    def test_load_fail(self):
        for state in list[TokenStream]([
            TokenStream(),
            TokenStream([Token('float', '3.14')]),
            TokenStream([Token('int', '1')]),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    And([Int.load, Int.load])(Scope[Val](), state)


class OrTest(TestCase):
    def test_load(self):
        for state, expected in list[tuple[TokenStream, StateAndResult[Val]]]([
            (
                TokenStream([
                    Token('int', '1'),
                ]),
                (
                    TokenStream(),
                    Int(1),
                )
            ),
            (
                TokenStream([
                    Token('str', 'a'),
                ]),
                (
                    TokenStream(),
                    Str('a'),
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('float', '3.14'),
                ]),
                (
                    TokenStream([Token('float', '3.14')]),
                    Int(1),
                )
            ),
            (
                TokenStream([
                    Token('str', 'a'),
                    Token('float', '3.14')
                ]),
                (
                    TokenStream([Token('float', '3.14')]),
                    Str('a'),
                )
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    Val.load(Scope[Val](), state),
                    expected
                )

    def test_load_fail(self):
        for state in list[TokenStream]([
            TokenStream(),
            TokenStream([Token('float', '3.14')]),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    Val.load(Scope[Val](), state)


class ZeroOrMoreTest(TestCase):
    def test_load(self):
        for state, expected in list[tuple[TokenStream, StateAndMultipleResult[Val]]]([
            (
                TokenStream([
                ]),
                (
                    TokenStream(),
                    [
                    ]
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                ]),
                (
                    TokenStream(),
                    [
                        Int(1),
                    ]
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('int', '2'),
                ]),
                (
                    TokenStream(),
                    [
                        Int(1),
                        Int(2),
                    ]
                )
            ),
            (
                TokenStream([
                    Token('float', '3.14'),
                ]),
                (
                    TokenStream([
                        Token('float', '3.14'),
                    ]),
                    [
                    ]
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('float', '3.14'),
                ]),
                (
                    TokenStream([
                        Token('float', '3.14'),
                    ]),
                    [
                        Int(1),
                    ]
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('int', '2'),
                    Token('float', '3.14'),
                ]),
                (
                    TokenStream([
                        Token('float', '3.14'),
                    ]),
                    [
                        Int(1),
                        Int(2),
                    ]
                )
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    ZeroOrMore(Int.load)(Scope[Val](), state),
                    expected
                )


class OneOrMoreTest(TestCase):
    def test_load(self):
        for state, expected in list[tuple[TokenStream, StateAndMultipleResult[Val]]]([
            (
                TokenStream([
                    Token('int', '1'),
                ]),
                (
                    TokenStream(),
                    [
                        Int(1),
                    ]
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('int', '2'),
                ]),
                (
                    TokenStream(),
                    [
                        Int(1),
                        Int(2),
                    ]
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('float', '3.14'),
                ]),
                (
                    TokenStream([
                        Token('float', '3.14'),
                    ]),
                    [
                        Int(1),
                    ]
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('int', '2'),
                    Token('float', '3.14'),
                ]),
                (
                    TokenStream([
                        Token('float', '3.14'),
                    ]),
                    [
                        Int(1),
                        Int(2),
                    ]
                )
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    OneOrMore(Int.load)(Scope[Val](), state),
                    expected
                )

    def test_load_fail(self):
        for state in list[TokenStream]([
            TokenStream(),
            TokenStream([Token('float', '3.14')]),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    OneOrMore(Int.load)(Scope[Val](), state)


class ZeroOrOneTest(TestCase):
    def test_load(self):
        for state, expected in list[tuple[TokenStream, StateAndOptionalResult[Val]]]([
            (
                TokenStream([
                ]),
                (
                    TokenStream(),
                    None,
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                ]),
                (
                    TokenStream(),
                    Int(1),
                )
            ),
            (
                TokenStream([
                    Token('float', '3.14'),
                ]),
                (
                    TokenStream([
                        Token('float', '3.14'),
                    ]),
                    None,
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('float', '3.14'),
                ]),
                (
                    TokenStream([
                        Token('float', '3.14'),
                    ]),
                    Int(1),
                )
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    ZeroOrOne(Int.load)(Scope[Val](), state),
                    expected
                )


class UntilEmptyTest(TestCase):
    def test_load(self):
        for state, expected in list[tuple[TokenStream, StateAndMultipleResult[Val]]]([
            (
                TokenStream([
                ]),
                (
                    TokenStream(),
                    [
                    ]
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                ]),
                (
                    TokenStream(),
                    [
                        Int(1),
                    ]
                )
            ),
            (
                TokenStream([
                    Token('int', '1'),
                    Token('int', '2'),
                ]),
                (
                    TokenStream(),
                    [
                        Int(1),
                        Int(2),
                    ]
                )
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    UntilEmpty(Int.load)(Scope[Val](), state),
                    expected
                )

    def test_load_fail(self):
        for state in list[TokenStream]([
            TokenStream([
                Token('float', '3.14'),
            ]),
            TokenStream([
                Token('int', '1'),
                Token('float', '3.14'),
            ]),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    UntilEmpty(Int.load)(Scope[Val](), state)
