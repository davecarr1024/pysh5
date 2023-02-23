import unittest
from .state import *


class CharTest(unittest.TestCase):
    def test_ctor(self):
        Char('a')

    def test_ctor_fail(self):
        for val in list[str](['', 'aa']):
            with self.subTest(val=val):
                with self.assertRaises(Error):
                    Char(val)


class StateTest(unittest.TestCase):
    def test_bool(self):
        for state, expected in list[tuple[State, bool]]([
            (State(), False),
            (State([Char('a')]), True)
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEquals(bool(state), expected)

    def test_head(self):
        for state, expected in list[tuple[State, Char]]([
            (State([Char('a')]), Char('a')),
            (State([Char('a'), Char('b')]), Char('a')),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(state.head(), expected)

    def test_head_fail(self):
        with self.assertRaises(Error):
            State().head()

    def test_tail(self):
        for state, expected in list[tuple[State, State]]([
            (
                State([Char('a')]),
                State(),
            ),
            (
                State([Char('a'), Char('b')]),
                State([Char('b')]),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(state.tail(), expected)

    def test_tail_fail(self):
        with self.assertRaises(Error):
            State().tail()


class ResultTest(unittest.TestCase):
    def test_add(self):
        for lhs, rhs, expected in list[tuple[Result, Result, Result]]([
            (Result(), Result(), Result()),
            (Result('a'), Result(), Result('a')),
            (Result(), Result('a'), Result('a')),
            (Result('a'), Result('b'), Result('ab')),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                self.assertEqual(lhs + rhs, expected)
