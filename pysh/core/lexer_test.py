from typing import Optional, Sequence
from unittest import TestCase
from . import chars, errors, lexer, regex, tokens


class LexerTest(TestCase):
    def test_call(self):
        for lexer_, state, expected in list[tuple[lexer.Lexer, str, Optional[tokens.TokenStream]]]([
            (
                lexer.Lexer([
                    lexer.Rule('r', regex.literal('a')),
                ]),
                'aa',
                tokens.TokenStream([
                    tokens.Token('r', 'a', chars.Position(0, 0)),
                    tokens.Token('r', 'a', chars.Position(0, 1)),
                ])
            ),
            (
                lexer.Lexer([
                    lexer.Rule('r', regex.literal('a')),
                ]),
                'ab',
                None
            ),
            (
                lexer.Lexer([
                    lexer.Rule('r', regex.literal('a')),
                    lexer.Rule('s', regex.literal('b')),
                ]),
                'ab',
                tokens.TokenStream([
                    tokens.Token('r', 'a', chars.Position(0, 0)),
                    tokens.Token('s', 'b', chars.Position(0, 1)),
                ])
            ),
            (
                lexer.Lexer([
                    lexer.Rule('r', regex.literal('a')),
                    lexer.Rule('s', regex.literal('b')),
                ]),
                'c',
                None
            ),
            (
                lexer.Lexer([
                    lexer.Rule('r', regex.literal('a')),
                    lexer.Rule('s', regex.literal('b')),
                    lexer.Rule(
                        'ws',
                        regex.Skip(
                            regex.Whitespace()
                        )
                    ),
                ]),
                'a b',
                tokens.TokenStream([
                    tokens.Token('r', 'a', chars.Position(0, 0)),
                    tokens.Token('s', 'b', chars.Position(0, 2)),
                ])
            ),
        ]):
            with self.subTest(lexer_=lexer_, state=state, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        lexer_(state)
                else:
                    self.assertEqual(lexer_(state), expected)

    def test_literals(self):
        for vals, expected in list[tuple[Sequence[str], lexer.Lexer]]([
            (
                [],
                lexer.Lexer(),
            ),
            (
                'abc',
                lexer.Lexer([
                    lexer.Rule('a', regex.literal('a')),
                    lexer.Rule('b', regex.literal('b')),
                    lexer.Rule('c', regex.literal('c')),
                ]),
            ),
            (
                ['ab', 'cd'],
                lexer.Lexer([
                    lexer.Rule('ab', regex.literal('ab')),
                    lexer.Rule('cd', regex.literal('cd')),
                ]),
            ),
        ]):
            with self.subTest(vals=vals, expected=expected):
                self.assertEqual(lexer.Lexer.literal(*vals), expected)

    def test_or(self):
        for lhs, rhs, expected in list[tuple[lexer.Lexer, lexer.Lexer, Optional[lexer.Lexer]]]([
            (
                lexer.Lexer([]),
                lexer.Lexer([]),
                lexer.Lexer([]),
            ),
            (
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                ]),
                lexer.Lexer([]),
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                ]),
            ),
            (
                lexer.Lexer([
                ]),
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                ]),
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                ]),
            ),
            (
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                ]),
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                ]),
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                ]),
            ),
            (
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                ]),
                lexer.Lexer([
                    lexer.Rule.load('r', 'b'),
                ]),
                None,
            ),
            (
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                ]),
                lexer.Lexer([
                    lexer.Rule.load('s', 'b'),
                ]),
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                    lexer.Rule.load('s', 'b'),
                ]),
            ),
            (
                lexer.Lexer([
                    lexer.Rule.load('s', 'b'),
                ]),
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                ]),
                lexer.Lexer([
                    lexer.Rule.load('s', 'b'),
                    lexer.Rule.load('r', 'a'),
                ]),
            ),
            (
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                    lexer.Rule.load('s', 'b'),
                ]),
                lexer.Lexer([
                    lexer.Rule.load('t', 'c'),
                    lexer.Rule.load('s', 'b'),
                ]),
                lexer.Lexer([
                    lexer.Rule.load('r', 'a'),
                    lexer.Rule.load('s', 'b'),
                    lexer.Rule.load('t', 'c'),
                ]),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        _ = lhs | rhs
                else:
                    self.assertEqual(lhs | rhs, expected)
