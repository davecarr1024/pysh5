from unittest import TestCase
from . import builtins_, vals


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
