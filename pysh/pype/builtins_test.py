from typing import Optional
from unittest import TestCase
from . import builtins_, classes, vals
from ..core import errors, parser, tokens


class IntTest(TestCase):
    def test_ctor(self):
        self.assertEqual(builtins_.int_(1), builtins_.int_(1))
        self.assertNotEqual(builtins_.int_(1), builtins_.int_(2))

    def test_binary_func(self):
        for lhs, rhs, func_name, expected in list[tuple[vals.Val, vals.Val, str, vals.Val]]([
            (
                builtins_.int_(1),
                builtins_.int_(2),
                '__add__',
                builtins_.int_(3),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, func_name=func_name, expected=expected):
                self.assertEqual(
                    lhs[func_name](vals.Scope(), vals.Args([vals.Arg(rhs)])),
                    expected
                )


class ObjectTest(TestCase):
    def test_load(self):
        for state, expected in list[tuple[str, Optional[parser.StateAndResult[classes.Object]]]]([
            (
                '1',
                (
                    tokens.TokenStream([]),
                    builtins_.int_(1),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        builtins_.Object.parser_()(state)
                else:
                    self.assertEqual(
                        builtins_.Object.parser_()(state), expected)
