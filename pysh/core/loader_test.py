from typing import Optional
from unittest import TestCase
from .loader import *
from . import errors


class LoaderTest(TestCase):
    def test_load_regex(self):
        for input, expected in list[tuple[str, Optional[regex.Regex]]]([
            (
                'a',
                regex.literal('a'),
            ),
            (
                'ab',
                regex.literal('ab'),
            ),
            (
                '(a)',
                regex.literal('a'),
            ),
            (
                '(ab)',
                regex.literal('ab'),
            ),
            (
                '(a|b)',
                regex.Or([
                    regex.literal('a'),
                    regex.literal('b'),
                ]),
            ),
        ]):
            with self.subTest(input=input, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        load_regex(input)
                else:
                    self.assertEqual(load_regex(input), expected)
