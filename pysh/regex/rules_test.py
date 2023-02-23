import unittest
from .rules import *


def _state(s: str = '') -> CharStream:
    return CharStream.load(s)


def _result(s: str = '') -> Result:
    return Result(_state(s).chars)


class ResultTest(unittest.TestCase):
    def test_add(self):
        for lhs, rhs, expected in list[tuple[Result, Result, Result]]([
            (_result(), _result(), _result()),
            (_result('a'), _result(), _result('a')),
            (_result(), _result('a'), _result('a')),
            (_result('a'), _result('b'), _result('ab')),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                self.assertEqual(lhs + rhs, expected)


class LiteralTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[CharStream, StateAndResult]]([
            (
                _state('a'),
                (
                    _state(),
                    _result('a'),
                ),
            ),
            (
                _state('ab'),
                (
                    _state('b'),
                    _result('a'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(Literal(Char('a'))(state), expected)

    def test_call_fail(self):
        for state in list[CharStream]([
            _state(),
            _state('b'),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    Literal(Char('a'))(state)


class AndTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[CharStream, StateAndResult]]([
            (
                _state('ab'),
                (
                    _state(),
                    _result('ab'),
                ),
            ),
            (
                _state('abc'),
                (
                    _state('c'),
                    _result('ab'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    And([Literal(Char('a')), Literal(Char('b'))])(state),
                    expected
                )

    def test_call_fail(self):
        for state in list[CharStream]([
            _state(),
            _state('b'),
            _state('ac'),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    And([Literal(Char('a')), Literal(Char('b'))])(state)


class OrTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[CharStream, StateAndResult]]([
            (
                _state('a'),
                (
                    _state(),
                    _result('a'),
                ),
            ),
            (
                _state('b'),
                (
                    _state(),
                    _result('b'),
                ),
            ),
            (
                _state('ac'),
                (
                    _state('c'),
                    _result('a'),
                ),
            ),
            (
                _state('bc'),
                (
                    _state('c'),
                    _result('b'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    Or([Literal(Char('a')), Literal(Char('b'))])(state),
                    expected
                )

    def test_call_fail(self):
        for state in list[CharStream]([
            _state(),
            _state('c'),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    Or([Literal(Char('a')), Literal(Char('b'))])(state)


class ZeroOrMoreTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[CharStream, StateAndResult]]([
            (
                _state(),
                (
                    _state(),
                    _result(),
                )
            ),
            (
                _state('a'),
                (
                    _state(),
                    _result('a'),
                ),
            ),
            (
                _state('aa'),
                (
                    _state(),
                    _result('aa'),
                ),
            ),
            (
                _state('b'),
                (
                    _state('b'),
                    _result(''),
                ),
            ),
            (
                _state('aab'),
                (
                    _state('b'),
                    _result('aa'),
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
        for state, expected in list[tuple[CharStream, StateAndResult]]([
            (
                _state('a'),
                (
                    _state(),
                    _result('a'),
                ),
            ),
            (
                _state('aa'),
                (
                    _state(),
                    _result('aa'),
                ),
            ),
            (
                _state('aab'),
                (
                    _state('b'),
                    _result('aa'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    OneOrMore(Literal(Char('a')))(state),
                    expected
                )

    def test_call_fail(self):
        for state in list[CharStream]([
            _state(),
            _state('b'),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    OneOrMore(Literal(Char('a')))(state)


class ZeroOrOneTest(unittest.TestCase):
    def test_call(self):
        for state, expected in list[tuple[CharStream, StateAndResult]]([
            (
                _state(),
                (
                    _state(),
                    _result(),
                )
            ),
            (
                _state('a'),
                (
                    _state(),
                    _result('a'),
                ),
            ),
            (
                _state('b'),
                (
                    _state('b'),
                    _result(''),
                ),
            ),
            (
                _state('ab'),
                (
                    _state('b'),
                    _result('a'),
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
        for state, expected in list[tuple[CharStream, StateAndResult]]([
            (
                _state(),
                (
                    _state(),
                    _result(),
                ),
            ),
            (
                _state('a'),
                (
                    _state(),
                    _result('a'),
                ),
            ),
            (
                _state('aa'),
                (
                    _state(),
                    _result('aa'),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(
                    UntilEmpty(Literal(Char('a')))(state),
                    expected
                )

    def test_call_fail(self):
        for state in list[CharStream]([
            _state('b'),
        ]):
            with self.subTest(state=state):
                with self.assertRaises(Error):
                    UntilEmpty(Literal(Char('a')))(state)
