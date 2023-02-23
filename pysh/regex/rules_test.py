import unittest
from .rules import *


class LiteralTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[State, StateAndResult]]([
            (
                State.load('a'),
                (
                    State(),
                    Result('a'),
                ),
            ),
            (
                State.load('ab'),
                (
                    State.load('b'),
                    Result('a'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(Literal(Char('a'))(state), expected)

    def test_call_fail(self):
        for state in list[State]([
            State(),
            State.load('b'),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    Literal(Char('a'))(state)


class AndTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[State, StateAndResult]]([
            (
                State.load('ab'),
                (
                    State(),
                    Result('ab'),
                ),
            ),
            (
                State.load('abc'),
                (
                    State.load('c'),
                    Result('ab'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    And([Literal(Char('a')), Literal(Char('b'))])(state),
                    expected
                )

    def test_call_fail(self):
        for state in list[State]([
            State(),
            State.load('b'),
            State.load('ac'),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    And([Literal(Char('a')), Literal(Char('b'))])(state)


class OrTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[State, StateAndResult]]([
            (
                State.load('a'),
                (
                    State(),
                    Result('a'),
                ),
            ),
            (
                State.load('b'),
                (
                    State(),
                    Result('b'),
                ),
            ),
            (
                State.load('ac'),
                (
                    State.load('c'),
                    Result('a'),
                ),
            ),
            (
                State.load('bc'),
                (
                    State.load('c'),
                    Result('b'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    Or([Literal(Char('a')), Literal(Char('b'))])(state),
                    expected
                )

    def test_call_fail(self):
        for state in list[State]([
            State(),
            State.load('c'),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    Or([Literal(Char('a')), Literal(Char('b'))])(state)


class ZeroOrMoreTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[State, StateAndResult]]([
            (
                State(),
                (
                    State(),
                    Result(),
                )
            ),
            (
                State.load('a'),
                (
                    State(),
                    Result('a'),
                ),
            ),
            (
                State.load('aa'),
                (
                    State(),
                    Result('aa'),
                ),
            ),
            (
                State.load('b'),
                (
                    State.load('b'),
                    Result(''),
                ),
            ),
            (
                State.load('aab'),
                (
                    State.load('b'),
                    Result('aa'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    ZeroOrMore(Literal(Char('a')))(state),
                    expected
                )


class OneOrMoreTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[State, StateAndResult]]([
            (
                State.load('a'),
                (
                    State(),
                    Result('a'),
                ),
            ),
            (
                State.load('aa'),
                (
                    State(),
                    Result('aa'),
                ),
            ),
            (
                State.load('aab'),
                (
                    State.load('b'),
                    Result('aa'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    OneOrMore(Literal(Char('a')))(state),
                    expected
                )

    def test_call_fail(self):
        for state in list[State]([
            State(),
            State.load('b'),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    OneOrMore(Literal(Char('a')))(state)


class ZeroOrOneTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[State, StateAndResult]]([
            (
                State(),
                (
                    State(),
                    Result(),
                )
            ),
            (
                State.load('a'),
                (
                    State(),
                    Result('a'),
                ),
            ),
            (
                State.load('b'),
                (
                    State.load('b'),
                    Result(''),
                ),
            ),
            (
                State.load('ab'),
                (
                    State.load('b'),
                    Result('a'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    ZeroOrOne(Literal(Char('a')))(state),
                    expected
                )


class UntilEmptyTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[State, StateAndResult]]([
            (
                State(),
                (
                    State(),
                    Result(),
                ),
            ),
            (
                State.load('a'),
                (
                    State(),
                    Result('a'),
                ),
            ),
            (
                State.load('aa'),
                (
                    State(),
                    Result('aa'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    UntilEmpty(Literal(Char('a')))(state),
                    expected
                )

    def test_call_fail(self):
        for state in list[State]([
            State.load('b'),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    UntilEmpty(Literal(Char('a')))(state)
