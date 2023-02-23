import unittest
from .chars import *


class CharTest(unittest.TestCase):
    def test_ctor(self):
        Char('a')

    def test_ctor_fail(self):
        for val in list[str](['', 'aa']):
            with self.subTest(val=val):
                with self.assertRaises(Error):
                    Char(val)


class CharStreamTest(unittest.TestCase):
    def test_bool(self):
        for state, expected in list[tuple[CharStream, bool]]([
            (CharStream(), False),
            (CharStream([Char('a')]), True)
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEquals(bool(state), expected)

    def test_head(self):
        for state, expected in list[tuple[CharStream, Char]]([
            (CharStream([Char('a')]), Char('a')),
            (CharStream([Char('a'), Char('b')]), Char('a')),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(state.head(), expected)

    def test_head_fail(self):
        with self.assertRaises(Error):
            CharStream().head()

    def test_tail(self):
        for state, expected in list[tuple[CharStream, CharStream]]([
            (
                CharStream([Char('a')]),
                CharStream(),
            ),
            (
                CharStream([Char('a'), Char('b')]),
                CharStream([Char('b')]),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(state.tail(), expected)

    def test_tail_fail(self):
        with self.assertRaises(Error):
            CharStream().tail()
