from typing import Optional, Sequence
from unittest import TestCase
from . import chars, errors, tokens


class TokenTest(TestCase):
    def test_load(self):
        for rule_name, val, expected in list[tuple[str, Sequence[chars.Char] | chars.CharStream, tokens.Token]]([
            (
                'r',
                [
                    chars.Char('a'),
                ],
                tokens.Token('r', 'a'),
            ),
            (
                'r',
                [
                    chars.Char('a'),
                    chars.Char('b'),
                ],
                tokens.Token('r', 'ab'),
            ),
            (
                'r',
                [
                    chars.Char('a', chars.Position(1, 2)),
                ],
                tokens.Token('r', 'a', chars.Position(1, 2)),
            ),
            (
                'r',
                [
                    chars.Char('a', chars.Position(1, 2)),
                    chars.Char('b', chars.Position(1, 3)),
                ],
                tokens.Token('r', 'ab', chars.Position(1, 2)),
            ),
            (
                'r',
                chars.CharStream([
                    chars.Char('a'),
                    chars.Char('b'),
                ]),
                tokens.Token('r', 'ab'),
            )
        ]):
            with self.subTest(rule_name=rule_name, val=val, expected=expected):
                self.assertEqual(
                    tokens.Token.load(rule_name, val),
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
                    tokens.Token.load(rule_name, val)


class TokensTest(TestCase):
    def test_add(self):
        for lhs, rhs, expected in list[tuple[tokens.TokenStream, tokens.TokenStream, tokens.TokenStream]]([
            (
                tokens.TokenStream([
                ]),
                tokens.TokenStream([
                ]),
                tokens.TokenStream([
                ]),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
                tokens.TokenStream([
                ]),
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
            ),
            (
                tokens.TokenStream([
                ]),
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
                tokens.TokenStream([
                    tokens.Token('s', 'b'),
                ]),
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                    tokens.Token('s', 'b'),
                ]),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                self.assertEqual(lhs+rhs, expected)

    def test_head(self):
        for stream, expected in list[tuple[tokens.TokenStream, tokens.Token]]([
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
                tokens.Token('r', 'a'),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                tokens.Token('r', 'a'),
            ),
        ]):
            with self.subTest(stream=stream, expected=expected):
                self.assertEqual(stream.head(), expected)

    def test_head_fail(self):
        with self.assertRaises(errors.Error):
            tokens.TokenStream().head()

    def test_tail(self):
        for stream, expected in list[tuple[tokens.TokenStream, tokens.TokenStream]]([
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
                tokens.TokenStream([
                ]),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                tokens.TokenStream([
                    tokens.Token('s', 'b'),
                ]),
            ),
        ]):
            with self.subTest(stream=stream, expected=expected):
                self.assertEqual(stream.tail(), expected)

    def test_tail_fail(self):
        with self.assertRaises(errors.Error):
            tokens.TokenStream().tail()

    def test_pop(self):
        for stream, rule_name, expected in list[tuple[tokens.TokenStream, Optional[str], tuple[tokens.TokenStream, tokens.Token]]]([
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
                'r',
                (
                    tokens.TokenStream(),
                    tokens.Token('r', 'a'),
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                'r',
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    tokens.Token('r', 'a'),
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                ]),
                None,
                (
                    tokens.TokenStream(),
                    tokens.Token('r', 'a'),
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('r', 'a'),
                    tokens.Token('s', 'b'),
                ]),
                None,
                (
                    tokens.TokenStream([
                        tokens.Token('s', 'b'),
                    ]),
                    tokens.Token('r', 'a'),
                ),
            ),
        ]):
            with self.subTest(stream=stream, rule_name=rule_name, expected=expected):
                self.assertEqual(stream.pop(rule_name), expected)

    def test_pop_fail(self):
        for stream, rule_name in list[tuple[tokens.TokenStream, Optional[str]]]([
            (
                tokens.TokenStream(),
                None,
            ),
            (
                tokens.TokenStream(),
                'r',
            ),
            (
                tokens.TokenStream([
                    tokens.Token('s', 'a'),
                ]),
                'r',
            ),
        ]):
            with self.subTest(stream=stream, rule_name=rule_name):
                with self.assertRaises(errors.Error):
                    stream.pop(rule_name)
