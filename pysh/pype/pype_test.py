from typing import Optional
from unittest import TestCase
from . import builtins_, pype, vals
from ..core import errors


class PypeTest(TestCase):
    def test_eval(self):
        for input, expected in list[tuple[str, Optional[vals.Val]]]([
            (
                '1;',
                builtins_.int_(1),
            ),
            (
                'a = 1; a;',
                builtins_.int_(1),
            ),
        ]):
            with self.subTest(input=input, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        pype.eval(input)
                else:
                    self.assertEqual(pype.eval(input), expected)
