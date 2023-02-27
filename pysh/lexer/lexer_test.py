from unittest import TestCase
from .lexer import *


class LexerTest(TestCase):
    def test_call(self):
        for lexer, input, expected in list[tuple[Lexer, str, TokenStream]]([
            (
                Lexer([
                    Rule('r', regex.literal('a')),
                    Rule('s', regex.literal('b')),
                ]),
                '',
                TokenStream(),
            ),
            (
                Lexer([
                    Rule('r', regex.literal('a')),
                    Rule('s', regex.literal('b')),
                ]),
                '',
                TokenStream(),
            ),
            (
                Lexer([
                    Rule('r', regex.literal('a')),
                    Rule('s', regex.literal('b')),
                ]),
                'a',
                TokenStream([Token('r', 'a')]),
            ),
            (
                Lexer([
                    Rule('r', regex.literal('a')),
                    Rule('s', regex.literal('b')),
                ]),
                'b',
                TokenStream([Token('s', 'b')]),
            ),
            (
                Lexer([
                    Rule('r', regex.literal('a')),
                    Rule('s', regex.literal('b')),
                ]),
                'ab',
                TokenStream([Token('r', 'a'), Token('s', 'b')]),
            ),
        ]):
            with self.subTest(lexer=lexer, input=input, expected=expected):
                self.assertEqual(lexer(input), expected)

    def test_call_fail(self):
        for lexer, input in list[tuple[Lexer, str]]([
            (
                Lexer([
                    Rule('r', regex.literal('a')),
                    Rule('s', regex.literal('b')),
                ]),
                'c',
            ),
        ]):
            with self.subTest(lexer=lexer, input=input):
                with self.assertRaises(LexError):
                    lexer(input)
