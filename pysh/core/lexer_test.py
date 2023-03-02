from typing import Optional
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
        ]):
            with self.subTest(lexer_=lexer_, state=state, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        lexer_(state)
                else:
                    self.assertEqual(lexer_(state), expected)
