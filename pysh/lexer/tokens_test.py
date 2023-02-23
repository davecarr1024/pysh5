from unittest import TestCase
from .tokens import *


class TokenTest(TestCase):
    def test_load_chars(self):
        self.assertEqual(
            Token.load(
                'r',
                CharStream.load(
                    'abc',
                    Position(10, 11),
                ).chars
            ),
            Token('r', 'abc', Position(10, 11))
        )

    def test_load_charstream(self):
        self.assertEqual(
            Token.load('r',
                       CharStream.load(
                           'abc',
                           Position(10, 11),
                       )
                       ),
            Token('r', 'abc', Position(10, 11))
        )

    def test_load_regex_result(self):
        self.assertEqual(
            Token.load('r',
                       regex.Result([Char('a'), Char('b')])
                       ),
            Token('r', 'ab')
        )


def _ts(*vals: str) -> TokenStream:
    return TokenStream([Token('r', val) for val in vals])


class TokenStreamTest(TestCase):
    def test_bool(self):
        for stream, expected in list[tuple[TokenStream, bool]]([
            (TokenStream(), False),
            (TokenStream([Token('r', 'a')]), True),
        ]):
            with self.subTest(stream=stream, expected=expected):
                self.assertEqual(bool(stream), expected)

    def test_add(self):
        for lhs, rhs, expected in list[tuple[TokenStream, TokenStream, TokenStream]]([
            (_ts(), _ts(), _ts()),
            (_ts('a'), _ts(), _ts('a')),
            (_ts(), _ts('a'), _ts('a')),
            (_ts('a'), _ts('b'), _ts('a', 'b')),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                self.assertEqual(lhs+rhs, expected)

    def test_concat(self):
        for streams, expected in list[tuple[list[TokenStream], TokenStream]]([
            (
                [],
                _ts(),
            ),
            (
                [_ts('a'), _ts('b'), _ts('c')],
                _ts('a', 'b', 'c'),
            ),
        ]):
            with self.subTest(streams=streams, expected=expected):
                self.assertEqual(TokenStream.concat(streams), expected)

    def test_head(self):
        for stream, expected in list[tuple[TokenStream, Token]]([
            (_ts('a'), Token('r', 'a')),
            (_ts('a', 'b'), Token('r', 'a')),
        ]):
            with self.subTest(stream=stream, expected=expected):
                self.assertEqual(stream.head(), expected)

    def test_head_fail(self):
        with self.assertRaises(Error):
            _ts().head()

    def test_tail(self):
        for stream, expected in list[tuple[TokenStream, TokenStream]]([
            (_ts('a'), _ts()),
            (_ts('a', 'b'), _ts('b')),
            (_ts('a', 'b', 'c'), _ts('b', 'c')),
        ]):
            with self.subTest(stream=stream, expected=expected):
                self.assertEqual(stream.tail(), expected)

    def test_tail_fail(self):
        with self.assertRaises(Error):
            _ts().tail()
