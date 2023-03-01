from typing import Optional, Sequence
from unittest import TestCase
from .tokens import *


class TokenTest(TestCase):
    def test_load(self):
        for rule_name, val, expected in list[tuple[str, Sequence[chars.Char] | chars.CharStream, Token]]([
            (
                'r',
                [
                    chars.Char('a'),
                ],
                Token('r', 'a'),
            ),
            (
                'r',
                [
                    chars.Char('a'),
                    chars.Char('b'),
                ],
                Token('r', 'ab'),
            ),
            (
                'r',
                [
                    chars.Char('a', chars.Position(1, 2)),
                ],
                Token('r', 'a', chars.Position(1, 2)),
            ),
            (
                'r',
                [
                    chars.Char('a', chars.Position(1, 2)),
                    chars.Char('b', chars.Position(1, 3)),
                ],
                Token('r', 'ab', chars.Position(1, 2)),
            ),
            (
                'r',
                chars.CharStream([
                    chars.Char('a'),
                    chars.Char('b'),
                ]),
                Token('r', 'ab'),
            )
        ]):
            with self.subTest(rule_name=rule_name, val=val, expected=expected):
                self.assertEqual(
                    Token.load(rule_name, val),
                    expected
                )

    def test_load_fail(self):
        for rule_name, val in list[tuple[str, Sequence[chars.Char] | chars.CharStream]]([
            (
                'r',
                [],
            ),
            (
                'r',
                chars.CharStream(),
            ),
        ]):
            with self.subTest(rule_name=rule_name, val=val):
                with self.assertRaises(errors.Error):
                    Token.load(rule_name, val)


class TokensTest(TestCase):
    def test_add(self):
        for lhs, rhs, expected in list[tuple[TokenStream, TokenStream, TokenStream]]([
            (
                TokenStream([
                ]),
                TokenStream([
                ]),
                TokenStream([
                ]),
            ),
            (
                TokenStream([
                    Token('r', 'a'),
                ]),
                TokenStream([
                ]),
                TokenStream([
                    Token('r', 'a'),
                ]),
            ),
            (
                TokenStream([
                ]),
                TokenStream([
                    Token('r', 'a'),
                ]),
                TokenStream([
                    Token('r', 'a'),
                ]),
            ),
            (
                TokenStream([
                    Token('r', 'a'),
                ]),
                TokenStream([
                    Token('s', 'b'),
                ]),
                TokenStream([
                    Token('r', 'a'),
                    Token('s', 'b'),
                ]),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                self.assertEqual(lhs+rhs, expected)

    def test_head(self):
        for stream, expected in list[tuple[TokenStream, Token]]([
            (
                TokenStream([
                    Token('r', 'a'),
                ]),
                Token('r', 'a'),
            ),
            (
                TokenStream([
                    Token('r', 'a'),
                    Token('s', 'b'),
                ]),
                Token('r', 'a'),
            ),
        ]):
            with self.subTest(stream=stream, expected=expected):
                self.assertEqual(stream.head(), expected)

    def test_head_fail(self):
        with self.assertRaises(errors.Error):
            TokenStream().head()

    def test_tail(self):
        for stream, expected in list[tuple[TokenStream, TokenStream]]([
            (
                TokenStream([
                    Token('r', 'a'),
                ]),
                TokenStream([
                ]),
            ),
            (
                TokenStream([
                    Token('r', 'a'),
                    Token('s', 'b'),
                ]),
                TokenStream([
                    Token('s', 'b'),
                ]),
            ),
        ]):
            with self.subTest(stream=stream, expected=expected):
                self.assertEqual(stream.tail(), expected)

    def test_tail_fail(self):
        with self.assertRaises(errors.Error):
            TokenStream().tail()

    def test_pop(self):
        for stream, rule_name, expected in list[tuple[TokenStream, Optional[str], tuple[TokenStream, Token]]]([
            (
                TokenStream([
                    Token('r', 'a'),
                ]),
                'r',
                (
                    TokenStream(),
                    Token('r', 'a'),
                ),
            ),
            (
                TokenStream([
                    Token('r', 'a'),
                    Token('s', 'b'),
                ]),
                'r',
                (
                    TokenStream([
                        Token('s', 'b'),
                    ]),
                    Token('r', 'a'),
                ),
            ),
            (
                TokenStream([
                    Token('r', 'a'),
                ]),
                None,
                (
                    TokenStream(),
                    Token('r', 'a'),
                ),
            ),
            (
                TokenStream([
                    Token('r', 'a'),
                    Token('s', 'b'),
                ]),
                None,
                (
                    TokenStream([
                        Token('s', 'b'),
                    ]),
                    Token('r', 'a'),
                ),
            ),
        ]):
            with self.subTest(stream=stream, rule_name=rule_name, expected=expected):
                self.assertEqual(stream.pop(rule_name), expected)

    def test_pop_fail(self):
        for stream, rule_name in list[tuple[TokenStream, Optional[str]]]([
            (
                TokenStream(),
                None,
            ),
            (
                TokenStream(),
                'r',
            ),
            (
                TokenStream([
                    Token('s', 'a'),
                ]),
                'r',
            ),
        ]):
            with self.subTest(stream=stream, rule_name=rule_name):
                with self.assertRaises(errors.Error):
                    stream.pop(rule_name)
