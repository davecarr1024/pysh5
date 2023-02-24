from unittest import TestCase
from .vals import *
from .builtins_ import *


class ScopeTest(TestCase):
    def test_set(self):
        s = Scope()
        self.assertNotIn('a', s)
        s['a'] = int_(1)
        self.assertIn('a', s)
        self.assertEqual(s['a'], int_(1))
        del s['a']
        self.assertNotIn('a', s)

    def test_as_child(self):
        p = Scope({'a': int_(1)})
        s = p.as_child({'a': int_(2), 'b': int_(3)})
        self.assertEqual(p['a'], int_(1))
        self.assertEqual(s['a'], int_(2))
        self.assertNotIn('b', p)
        self.assertEqual(s['b'], int_(3))
        self.assertDictEqual(
            p.all_vals,
            {'a': int_(1)}
        )
        self.assertDictEqual(
            s.all_vals,
            {'a': int_(2), 'b': int_(3)}
        )


class ArgsTest(TestCase):
    def test_len(self):
        for args, expected in list[tuple[Args, int]]([
            (Args([]), 0),
            (Args([Arg(int_(1))]), 1),
            (Args([Arg(int_(1)), Arg(int_(2))]), 2),
        ]):
            with self.subTest(args=args, expected=expected):
                self.assertEqual(len(args), expected)

    def test_prepend(self):
        self.assertEqual(
            Args([Arg(int_(1))]).prepend(Arg(int_(2))),
            Args([Arg(int_(2)), Arg(int_(1))])
        )


class ParamsTest(TestCase):
    def test_bind_fail(self):
        with self.assertRaises(Error):
            Params([]).bind(Scope(), Args([Arg(int_(1))]))

    def test_bind(self):
        for params, args, expected in list[tuple[Params, Args, Scope]]([
            (
                Params([
                ]),
                Args([
                ]),
                Scope({
                    'a': int_(1),
                })
            ),
            (
                Params([
                    Param('a'),
                ]),
                Args([
                    Arg(int_(2)),
                ]),
                Scope({
                    'a': int_(2),
                })
            ),
            (
                Params([
                    Param('b'),
                ]),
                Args([
                    Arg(int_(2)),
                ]),
                Scope({
                    'a': int_(1),
                    'b': int_(2),
                })
            ),
        ]):
            with self.subTest(params=params, args=args, expected=expected):
                self.assertEqual(params.bind(
                    Scope({'a': int_(1)}), args), expected)

    def test_tail_fail(self):
        with self.assertRaises(Error):
            Params([]).tail

    def test_tail(self):
        for params, expected in list[tuple[Params, Params]]([
            (
                Params([
                    Param('a'),
                ]),
                Params([
                ]),
            ),
            (
                Params([
                    Param('a'),
                    Param('b'),
                ]),
                Params([
                    Param('b'),
                ]),
            ),
        ]):
            with self.subTest(params=params, expected=expected):
                self.assertEqual(params.tail, expected)
