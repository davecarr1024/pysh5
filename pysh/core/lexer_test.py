from typing import Optional
from unittest import TestCase
from .lexer import *


class LexerTest(TestCase):
    def test_call(self):
        for lexer, state, expected in list[tuple[Lexer, str, Optional[tokens.TokenStream]]]([
            (
                Lexer([
                    Rule('r', regex.literal('a')),
                ]),
                'aa',
                tokens.TokenStream([
                    tokens.Token('r', 'a', chars.Position(0, 0)),
                    tokens.Token('r', 'a', chars.Position(0, 1)),
                ])
            ),
            (
                Lexer([
                    Rule('r', regex.literal('a')),
                ]),
                'ab',
                None
            ),
            (
                Lexer([
                    Rule('r', regex.literal('a')),
                    Rule('s', regex.literal('b')),
                ]),
                'ab',
                tokens.TokenStream([
                    tokens.Token('r', 'a', chars.Position(0, 0)),
                    tokens.Token('s', 'b', chars.Position(0, 1)),
                ])
            ),
            (
                Lexer([
                    Rule('r', regex.literal('a')),
                    Rule('s', regex.literal('b')),
                ]),
                'c',
                None
            ),
        ]):
            with self.subTest(lexer=lexer, state=state, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        lexer(state)
                else:
                    self.assertEqual(lexer(state), expected)
