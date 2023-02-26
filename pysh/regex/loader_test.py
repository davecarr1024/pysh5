from unittest import TestCase
from .loader import *


class LoaderTest(TestCase):
    def test_load(self):
        for input, expected in list[tuple[str, Rule]]([
            (
                'a',
                Literal(Char('a')),
            ),
            (
                'ab',
                And([
                    Literal(Char('a')),
                    Literal(Char('b')),
                ]),
            ),
            (
                '(a)',
                Literal(Char('a')),
            ),
            (
                '(ab)',
                And([
                    Literal(Char('a')),
                    Literal(Char('b')),
                ]),
            ),
            (
                'a|b',
                Or([
                    Literal(Char('a')),
                    Literal(Char('b')),
                ]),
            ),
            (
                '(a)|b',
                Or([
                    Literal(Char('a')),
                    Literal(Char('b')),
                ]),
            ),
            (
                'a*',
                ZeroOrMore(Literal(Char('a'))),
            ),
            (
                '(a)*',
                ZeroOrMore(Literal(Char('a'))),
            ),
            (
                'a+',
                OneOrMore(Literal(Char('a'))),
            ),
            (
                '(a)+',
                OneOrMore(Literal(Char('a'))),
            ),
            (
                'a?',
                ZeroOrOne(Literal(Char('a'))),
            ),
            (
                '(a)?',
                ZeroOrOne(Literal(Char('a'))),
            ),
            (
                'a!',
                UntilEmpty(Literal(Char('a'))),
            ),
            (
                '(a)!',
                UntilEmpty(Literal(Char('a'))),
            ),
            (
                '^a',
                Not(Literal(Char('a'))),
            ),
            (
                '^(a)',
                Not(Literal(Char('a'))),
            ),
            (
                '[a-z]',
                Class('a', 'z'),
            ),
            (
                '\\\\',
                Literal(Char('\\')),
            ),
        ]):
            with self.subTest(input=input, expected=expected):
                self.assertEqual(load(input), expected)
