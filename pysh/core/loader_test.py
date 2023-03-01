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
            (
                'a*',
                regex.ZeroOrMore(regex.literal('a')),
            ),
            (
                'a+',
                regex.OneOrMore(regex.literal('a')),
            ),
            (
                'a?',
                regex.ZeroOrOne(regex.literal('a')),
            ),
            (
                'a!',
                regex.UntilEmpty(regex.literal('a')),
            ),
            (
                '^a',
                regex.Not(regex.literal('a')),
            ),
            (
                '[a-z]',
                regex.Range('a', 'z'),
            ),
        ]):
            with self.subTest(input=input, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        load_regex(input)
                else:
                    self.assertEqual(load_regex(input), expected)
