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
                literal('a'),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                literal('a'),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream.load('b', chars.Position(0, 1)),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                literal('a'),
                chars.CharStream.load('b'),
                None
            ),
            (
                And([literal('a'), literal('b')]),
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
                And([literal('a'), literal('b')]),
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
                And([literal('a'), literal('b')]),
                chars.CharStream.load('c'),
                None
            ),
            (
                And([literal('a'), literal('b')]),
                chars.CharStream.load('b'),
                None
            ),
            (
                Or([literal('a'), literal('b')]),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                Or([literal('a'), literal('b')]),
                chars.CharStream.load('b'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('b'),
                    ])
                )
            ),
            (
                Or([literal('a'), literal('b')]),
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
                Or([literal('a'), literal('b')]),
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
                Or([literal('a'), literal('b')]),
                chars.CharStream.load('c'),
                None
            ),
            (
                ZeroOrMore(literal('a')),
                chars.CharStream.load(''),
                (
                    chars.CharStream(),
                    Result([
                    ])
                )
            ),
            (
                ZeroOrMore(literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                ZeroOrMore(literal('a')),
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
                ZeroOrMore(literal('a')),
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
                ZeroOrMore(literal('a')),
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
                ZeroOrMore(literal('a')),
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
                OneOrMore(literal('a')),
                chars.CharStream.load(''),
                None
            ),
            (
                OneOrMore(literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                OneOrMore(literal('a')),
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
                OneOrMore(literal('a')),
                chars.CharStream.load('b'),
                None
            ),
            (
                OneOrMore(literal('a')),
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
                OneOrMore(literal('a')),
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
                ZeroOrOne(literal('a')),
                chars.CharStream.load(''),
                (
                    chars.CharStream(),
                    Result([
                    ])
                )
            ),
            (
                ZeroOrOne(literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                ZeroOrOne(literal('a')),
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
                ZeroOrOne(literal('a')),
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
                UntilEmpty(literal('a')),
                chars.CharStream.load(''),
                (
                    chars.CharStream(),
                    Result([
                    ])
                )
            ),
            (
                UntilEmpty(literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                UntilEmpty(literal('a')),
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
                UntilEmpty(literal('a')),
                chars.CharStream.load('b'),
                None
            ),
            (
                UntilEmpty(literal('a')),
                chars.CharStream.load('ab'),
                None
            ),
            (
                UntilEmpty(literal('a')),
                chars.CharStream.load('aab'),
                None
            ),
            (
                Not(literal('a')),
                chars.CharStream.load('a'),
                None,
            ),
            (
                Not(literal('a')),
                chars.CharStream.load('b'),
                (
                    chars.CharStream(),
                    Result([
                    ])
                )
            ),
            (
                Not(literal('a')),
                chars.CharStream.load('bc'),
                (
                    chars.CharStream([
                        chars.Char('c', chars.Position(0, 1)),
                    ]),
                    Result([
                    ])
                )
            ),
            (
                Range('a', 'z'),
                chars.CharStream.load('a'),
                (
                    chars.CharStream([]),
                    Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                Range('a', 'z'),
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
                Range('a', 'z'),
                chars.CharStream.load('1'),
                None
            ),
        ]):
            with self.subTest(regex=regex, state=state, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        regex(state)
                else:
                    self.assertEqual(regex(state), expected)

    def test_loadliteral(self):
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
