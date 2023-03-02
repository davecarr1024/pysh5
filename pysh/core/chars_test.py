from unittest import TestCase
from . import chars, errors


class CharTest(TestCase):
    def test_ctor(self):
        chars.Char('a')

    def test_ctor_fail(self):
        for val in list[str](['', 'aa']):
            with self.subTest(val=val):
                with self.assertRaises(errors.Error):
                    chars.Char(val)


class CharStreamTest(TestCase):
    def test_bool(self):
        for state, expected in list[tuple[chars.CharStream, bool]]([
            (chars.CharStream(), False),
            (chars.CharStream([chars.Char('a')]), True)
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(bool(state), expected)

    def test_head(self):
        for state, expected in list[tuple[chars.CharStream, chars.Char]]([
            (chars.CharStream([chars.Char('a')]), chars.Char('a')),
            (chars.CharStream(
                [chars.Char('a'), chars.Char('b')]), chars.Char('a')),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(state.head(), expected)

    def test_head_fail(self):
        with self.assertRaises(errors.Error):
            chars.CharStream().head()

    def test_tail(self):
        for state, expected in list[tuple[chars.CharStream, chars.CharStream]]([
            (
                chars.CharStream([chars.Char('a')]),
                chars.CharStream(),
            ),
            (
                chars.CharStream([chars.Char('a'), chars.Char('b')]),
                chars.CharStream([chars.Char('b')]),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(state.tail(), expected)

    def test_tail_fail(self):
        with self.assertRaises(errors.Error):
            chars.CharStream().tail()
