from unittest import TestCase
from .lexer import *


class LexerTest(TestCase):
    def test_call(self):
        for lexer, input, expected in list[tuple[Lexer, str, TokenStream]]([
            (
                Lexer({
                    'r': regex.Literal(Char('a')),
                    's': regex.Literal(Char('b')),
                }),
                '',
                TokenStream(),
            ),
            (
                Lexer({
                    'r': regex.Literal(Char('a')),
                    's': regex.Literal(Char('b')),
                }),
                'a',
                TokenStream([Token('r', 'a')]),
            ),
            (
                Lexer({
                    'r': regex.Literal(Char('a')),
                    's': regex.Literal(Char('b')),
                }),
                'b',
                TokenStream([Token('s', 'b')]),
            ),
            (
                Lexer({
                    'r': regex.Literal(Char('a')),
                    's': regex.Literal(Char('b')),
                }),
                'ab',
                TokenStream([Token('r', 'a'), Token('s', 'b')]),
            ),
        ]):
            with self.subTest(lexer=lexer, input=input, expected=expected):
                self.assertEqual(lexer(input), expected)

    def test_call_fail(self):
        for lexer, input in list[tuple[Lexer, str]]([
            (
                Lexer({
                    'r': regex.Literal(Char('a')),
                    's': regex.Literal(Char('b')),
                }),
                'c',
            ),
        ]):
            with self.subTest(lexer=lexer, input=input):
                with self.assertRaises(LexError):
                    lexer(input)
