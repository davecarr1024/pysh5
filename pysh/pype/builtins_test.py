from unittest import TestCase
from .builtins_ import *


class IntTest(TestCase):
    def test_ctor(self):
        self.assertEqual(int_(1), int_(1))
        self.assertNotEqual(int_(1), int_(2))

    def test_binary_func(self):
        for lhs, rhs, func_name, expected in list[tuple[Val, Val, str, Val]]([
            (
                int_(1),
                int_(2),
                '__add__',
                int_(3),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, func_name=func_name, expected=expected):
                self.assertEqual(
                    lhs[func_name](Scope(), Args([Arg(rhs)])),
                    expected
                )
