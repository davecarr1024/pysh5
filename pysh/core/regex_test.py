from typing import Optional
from unittest import TestCase
from . import chars, errors, regex, tokens

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    __import__('sys').modules['unittest.util']._MAX_LENGTH = 999999999


class ResultTest(TestCase):
    def test_add(self):
        for lhs, rhs, expected in list[tuple[regex.Result, regex.Result, regex.Result]]([
            (
                regex.Result([
                ]),
                regex.Result([
                ]),
                regex.Result([
                ]),
            ),
            (
                regex.Result([
                    chars.Char('a'),
                ]),
                regex.Result([
                ]),
                regex.Result([
                    chars.Char('a'),
                ]),
            ),
            (
                regex.Result([
                ]),
                regex.Result([
                    chars.Char('a'),
                ]),
                regex.Result([
                    chars.Char('a'),
                ]),
            ),
            (
                regex.Result([
                    chars.Char('a'),
                ]),
                regex.Result([
                    chars.Char('b'),
                ]),
                regex.Result([
                    chars.Char('a'),
                    chars.Char('b'),
                ]),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                self.assertEqual(lhs+rhs, expected)

    def test_position(self):
        for result, expected in list[tuple[regex.Result, chars.Position]]([
            (
                regex.Result(),
                chars.Position(),
            ),
            (
                regex.Result([
                    chars.Char('a', chars.Position(1, 2)),
                ]),
                chars.Position(1, 2),
            ),
            (
                regex.Result([
                    chars.Char('a', chars.Position(1, 2)),
                    chars.Char('b', chars.Position(1, 3)),
                ]),
                chars.Position(1, 2),
            ),
        ]):
            with self.subTest(result=result, expected=expected):
                self.assertEqual(result.position(), expected)

    def test_val(self):
        for result, expected in list[tuple[regex.Result, str]]([
            (
                regex.Result(),
                '',
            ),
            (
                regex.Result([
                    chars.Char('a'),
                ]),
                'a',
            ),
            (
                regex.Result([
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
            regex.Result([
                chars.Char('a', chars.Position(1, 2)),
                chars.Char('b', chars.Position(3, 4)),
            ]).token('r'),
            tokens.Token('r', 'ab', chars.Position(1, 2))
        )


class RegexTest(TestCase):
    def test_call(self):
        for regex_, state, expected in list[tuple[regex.Regex, chars.CharStream, Optional[regex.StateAndResult]]]([
            (
                regex.Any(),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.Any(),
                chars.CharStream.load('a', chars.Position(1, 2)),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a', chars.Position(1, 2)),
                    ])
                )
            ),
            (
                regex.Any(),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream.load('b', chars.Position(0, 1)),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.literal('a'),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.literal('a'),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream.load('b', chars.Position(0, 1)),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.literal('a'),
                chars.CharStream.load('b'),
                None
            ),
            (
                regex.And([regex.literal('a'), regex.literal('b')]),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                        chars.Char('b', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                regex.And([regex.literal('a'), regex.literal('b')]),
                chars.CharStream.load('abc'),
                (
                    chars.CharStream([
                        chars.Char('c', chars.Position(0, 2)),
                    ]),
                    regex.Result([
                        chars.Char('a'),
                        chars.Char('b', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                regex.And([regex.literal('a'), regex.literal('b')]),
                chars.CharStream.load('c'),
                None
            ),
            (
                regex.And([regex.literal('a'), regex.literal('b')]),
                chars.CharStream.load('b'),
                None
            ),
            (
                regex.Or([regex.literal('a'), regex.literal('b')]),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.Or([regex.literal('a'), regex.literal('b')]),
                chars.CharStream.load('b'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('b'),
                    ])
                )
            ),
            (
                regex.Or([regex.literal('a'), regex.literal('b')]),
                chars.CharStream.load('ac'),
                (
                    chars.CharStream([
                        chars.Char('c', chars.Position(0, 1)),
                    ]),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.Or([regex.literal('a'), regex.literal('b')]),
                chars.CharStream.load('bc'),
                (
                    chars.CharStream([
                        chars.Char('c', chars.Position(0, 1)),
                    ]),
                    regex.Result([
                        chars.Char('b'),
                    ])
                )
            ),
            (
                regex.Or([regex.literal('a'), regex.literal('b')]),
                chars.CharStream.load('c'),
                None
            ),
            (
                regex.ZeroOrMore(regex.literal('a')),
                chars.CharStream.load(''),
                (
                    chars.CharStream(),
                    regex.Result([
                    ])
                )
            ),
            (
                regex.ZeroOrMore(regex.literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.ZeroOrMore(regex.literal('a')),
                chars.CharStream.load('aa'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                        chars.Char('a', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                regex.ZeroOrMore(regex.literal('a')),
                chars.CharStream.load('b'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 0)),
                    ]),
                    regex.Result([
                    ])
                )
            ),
            (
                regex.ZeroOrMore(regex.literal('a')),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 1)),
                    ]),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.ZeroOrMore(regex.literal('a')),
                chars.CharStream.load('aab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 2)),
                    ]),
                    regex.Result([
                        chars.Char('a'),
                        chars.Char('a', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                regex.OneOrMore(regex.literal('a')),
                chars.CharStream.load(''),
                None
            ),
            (
                regex.OneOrMore(regex.literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.OneOrMore(regex.literal('a')),
                chars.CharStream.load('aa'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                        chars.Char('a', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                regex.OneOrMore(regex.literal('a')),
                chars.CharStream.load('b'),
                None
            ),
            (
                regex.OneOrMore(regex.literal('a')),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 1)),
                    ]),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.OneOrMore(regex.literal('a')),
                chars.CharStream.load('aab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 2)),
                    ]),
                    regex.Result([
                        chars.Char('a'),
                        chars.Char('a', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                regex.ZeroOrOne(regex.literal('a')),
                chars.CharStream.load(''),
                (
                    chars.CharStream(),
                    regex.Result([
                    ])
                )
            ),
            (
                regex.ZeroOrOne(regex.literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.ZeroOrOne(regex.literal('a')),
                chars.CharStream.load('b'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 0)),
                    ]),
                    regex.Result([
                    ])
                )
            ),
            (
                regex.ZeroOrOne(regex.literal('a')),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 1)),
                    ]),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.UntilEmpty(regex.literal('a')),
                chars.CharStream.load(''),
                (
                    chars.CharStream(),
                    regex.Result([
                    ])
                )
            ),
            (
                regex.UntilEmpty(regex.literal('a')),
                chars.CharStream.load('a'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.UntilEmpty(regex.literal('a')),
                chars.CharStream.load('aa'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('a'),
                        chars.Char('a', chars.Position(0, 1)),
                    ])
                )
            ),
            (
                regex.UntilEmpty(regex.literal('a')),
                chars.CharStream.load('b'),
                None
            ),
            (
                regex.UntilEmpty(regex.literal('a')),
                chars.CharStream.load('ab'),
                None
            ),
            (
                regex.UntilEmpty(regex.literal('a')),
                chars.CharStream.load('aab'),
                None
            ),
            (
                regex.Not(regex.literal('a')),
                chars.CharStream.load('a'),
                None,
            ),
            (
                regex.Not(regex.literal('a')),
                chars.CharStream.load('b'),
                (
                    chars.CharStream(),
                    regex.Result([
                        chars.Char('b'),
                    ])
                )
            ),
            (
                regex.Not(regex.literal('a')),
                chars.CharStream.load('bc'),
                (
                    chars.CharStream([
                        chars.Char('c', chars.Position(0, 1)),
                    ]),
                    regex.Result([
                        chars.Char('b'),
                    ])
                )
            ),
            (
                regex.Range('a', 'z'),
                chars.CharStream.load('a'),
                (
                    chars.CharStream([]),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.Range('a', 'z'),
                chars.CharStream.load('ab'),
                (
                    chars.CharStream([
                        chars.Char('b', chars.Position(0, 1)),
                    ]),
                    regex.Result([
                        chars.Char('a'),
                    ])
                )
            ),
            (
                regex.Range('a', 'z'),
                chars.CharStream.load('1'),
                None
            ),
            (
                regex.Skip(regex.literal('ab')),
                chars.CharStream.load('abc'),
                (
                    chars.CharStream([
                        chars.Char('c', chars.Position(0, 2)),
                    ]),
                    regex.Result(),
                )
            ),
        ]):
            with self.subTest(regex_=regex_, state=state, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        regex_(state)
                else:
                    self.assertEqual(regex_(state), expected)

    def test_loadliteral(self):
        for val, expected in list[tuple[str, regex.Regex]]([
            (
                '',
                regex.And([]),
            ),
            (
                'a',
                regex.Literal('a'),
            ),
            (
                'ab',
                regex.And([
                    regex.Literal('a'),
                    regex.Literal('b'),
                ]),
            )
        ]):
            with self.subTest(val=val, expected=expected):
                self.assertEqual(regex.literal(val), expected)

    def test_load(self):
        for input, expected in list[tuple[str, Optional[regex.Regex]]]([
            (
                '',
                None,
            ),
            (
                'a',
                regex.literal('a'),
            ),
            (
                'ab',
                regex.literal('ab'),
            ),
            (
                '(ab)',
                regex.literal('ab'),
            ),
            (
                '(a)(b)',
                regex.literal('ab'),
            ),
            (
                '(a|b)',
                regex.Or([
                    regex.literal('a'),
                    regex.literal('b'),
                ]),
            ),
            (
                '(a|b|c)',
                regex.Or([
                    regex.literal('a'),
                    regex.literal('b'),
                    regex.literal('c'),
                ]),
            ),
            (
                '(a|(bc))',
                regex.Or([
                    regex.literal('a'),
                    regex.literal('bc'),
                ]),
            ),
            (
                '[a-z]',
                regex.Range('a', 'z'),
            ),
            (
                '.',
                regex.Any(),
            ),
            (
                '\\w',
                regex.Whitespace(),
            ),
            (
                '\\(',
                regex.literal('('),
            ),
            (
                '\\',
                None,
            ),
            (
                'a*',
                regex.ZeroOrMore(regex.literal('a')),
            ),
            (
                'a+',
                regex.OneOrMore(regex.literal('a')),
            ),
            (
                'a?',
                regex.ZeroOrOne(regex.literal('a')),
            ),
            (
                'a!',
                regex.UntilEmpty(regex.literal('a')),
            ),
            (
                '^a',
                regex.Not(regex.literal('a')),
            ),
            (
                '~a',
                regex.Skip(regex.literal('a')),
            ),
        ]):
            with self.subTest(input=input, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        regex.load(input)
                else:
                    self.assertEqual(regex.load(input), expected)
