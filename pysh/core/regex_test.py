from typing import Optional
from unittest import TestCase
from .regex import *


class ResultTest(TestCase):
    def test_add(self):
        for lhs, rhs, expected in list[tuple[Result, Result, Result]]([
            (
                Result([
                ]),
                Result([
                ]),
                Result([
                ]),
            ),
            (
                Result([
                    chars.Char('a'),
                ]),
                Result([
                ]),
                Result([
                    chars.Char('a'),
                ]),
            ),
            (
                Result([
                ]),
                Result([
                    chars.Char('a'),
                ]),
                Result([
                    chars.Char('a'),
                ]),
            ),
            (
                Result([
                    chars.Char('a'),
                ]),
                Result([
                    chars.Char('b'),
                ]),
                Result([
                    chars.Char('a'),
                    chars.Char('b'),
                ]),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                self.assertEqual(lhs+rhs, expected)

    def test_position(self):
        for result, expected in list[tuple[Result, chars.Position]]([
            (
                Result([
                    chars.Char('a', chars.Position(1, 2)),
                ]),
                chars.Position(1, 2),
            ),
            (
                Result([
                    chars.Char('a', chars.Position(1, 2)),
                    chars.Char('b', chars.Position(1, 3)),
                ]),
                chars.Position(1, 2),
            ),
        ]):
            with self.subTest(result=result, expected=expected):
                self.assertEqual(result.position(), expected)

    def test_position_fail(self):
        with self.assertRaises(errors.Error):
            Result().position()

    def test_val(self):
        for result, expected in list[tuple[Result, str]]([
            (
                Result(),
                '',
            ),
            (
                Result([
                    chars.Char('a'),
                ]),
                'a',
            ),
            (
                Result([
                    chars.Char('a'),
                    chars.Char('b'),
                ]),
                'ab',
            ),
        ]):
            with self.subTest(result=result, expected=expected):
                self.assertEqual(result.val(), expected)

    def test_token(self):
        self.assertEqual(
            Result([
                chars.Char('a', chars.Position(1, 2)),
                chars.Char('b', chars.Position(3, 4)),
            ]).token('r'),
            tokens.Token('r', 'ab', chars.Position(1, 2))
        )


class RegexTest(TestCase):
    def test_call(self):
        for regex, state, expected in list[tuple[Regex, chars.CharStream, Optional[StateAndResult]]]([
            (
                Any(),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                Any(),
                chars.CharStream.load('a', chars.Position(1, 2)),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a', chars.Position(1, 2)),
                    ])
                )
            ),
            (
                Any(),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream.load('b', chars.Position(0, 1)),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                Literal('a'),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                Literal('a'),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream.load('b', chars.Position(0, 1)),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                Literal('a'),
                chars.CharStream.load('b'),
                None
            ),
            (
                And([Literal('a'), Literal('b')]),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                        chars.Char('b', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                And([Literal('a'), Literal('b')]),
                chars.CharStream.load('abc'),
                (
                    chars.CharStream([
                        chars.Char('c', chars.Position(0, 2)),
                    ]),
                    Result([
                        chars.Char('a'),
                        chars.Char('b', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                And([Literal('a'), Literal('b')]),
                chars.CharStream.load('c'),
                None
            ),
            (
                And([Literal('a'), Literal('b')]),
                chars.CharStream.load('b'),
                None
            ),
            (
                Or([Literal('a'), Literal('b')]),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                Or([Literal('a'), Literal('b')]),
                chars.CharStream.load('b'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('b'),
                    ])
                )
            ),
            (
                Or([Literal('a'), Literal('b')]),
                chars.CharStream.load('ac'),
                (
                    chars.CharStream([
                        chars.Char('c', chars.Position(0, 1)),
                    ]),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                Or([Literal('a'), Literal('b')]),
                chars.CharStream.load('bc'),
                (
                    chars.CharStream([
                        chars.Char('c', chars.Position(0, 1)),
                    ]),
                    Result([
                        chars.Char('b'),
                    ])
                )
            ),
            (
                Or([Literal('a'), Literal('b')]),
                chars.CharStream.load('c'),
                None
            ),
            (
                ZeroOrMore(Literal('a')),
                chars.CharStream.load(''),
                (
                    chars.CharStream(),
                    Result([
                    ])
                )
            ),
            (
                ZeroOrMore(Literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                ZeroOrMore(Literal('a')),
                chars.CharStream.load('aa'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                        chars.Char('a', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                ZeroOrMore(Literal('a')),
                chars.CharStream.load('b'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 0)),
                    ]),
                    Result([
                    ])
                )
            ),
            (
                ZeroOrMore(Literal('a')),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 1)),
                    ]),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                ZeroOrMore(Literal('a')),
                chars.CharStream.load('aab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 2)),
                    ]),
                    Result([
                        chars.Char('a'),
                        chars.Char('a', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                OneOrMore(Literal('a')),
                chars.CharStream.load(''),
                None
            ),
            (
                OneOrMore(Literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                OneOrMore(Literal('a')),
                chars.CharStream.load('aa'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                        chars.Char('a', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                OneOrMore(Literal('a')),
                chars.CharStream.load('b'),
                None
            ),
            (
                OneOrMore(Literal('a')),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 1)),
                    ]),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                OneOrMore(Literal('a')),
                chars.CharStream.load('aab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 2)),
                    ]),
                    Result([
                        chars.Char('a'),
                        chars.Char('a', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                ZeroOrOne(Literal('a')),
                chars.CharStream.load(''),
                (
                    chars.CharStream(),
                    Result([
                    ])
                )
            ),
            (
                ZeroOrOne(Literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                ZeroOrOne(Literal('a')),
                chars.CharStream.load('b'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 0)),
                    ]),
                    Result([
                    ])
                )
            ),
            (
                ZeroOrOne(Literal('a')),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 1)),
                    ]),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                UntilEmpty(Literal('a')),
                chars.CharStream.load(''),
                (
                    chars.CharStream(),
                    Result([
                    ])
                )
            ),
            (
                UntilEmpty(Literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                UntilEmpty(Literal('a')),
                chars.CharStream.load('aa'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                        chars.Char('a', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                UntilEmpty(Literal('a')),
                chars.CharStream.load('b'),
                None
            ),
            (
                UntilEmpty(Literal('a')),
                chars.CharStream.load('ab'),
                None
            ),
            (
                UntilEmpty(Literal('a')),
                chars.CharStream.load('aab'),
                None
            ),
        ]):
            with self.subTest(regex=regex, state=state, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        regex(state)
                else:
                    self.assertEqual(regex(state), expected)

    def test_invalid_literal(self):
        for val in list[str]([
            '',
            'ab',
        ]):
            with self.subTest(val=val):
                with self.assertRaises(errors.Error):
                    Literal(val)

    def test_load_literal(self):
        for val, expected in list[tuple[str, Regex]]([
            (
                '',
                And([]),
            ),
            (
                'a',
                Literal('a'),
            ),
            (
                'ab',
                And([
                    Literal('a'),
                    Literal('b'),
                ]),
            )
        ]):
            with self.subTest(val=val, expected=expected):
                self.assertEqual(literal(val), expected)
