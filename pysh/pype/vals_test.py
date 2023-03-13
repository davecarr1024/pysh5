from unittest import TestCase
from . import builtins_,  vals
from ..core import errors


class ScopeTest(TestCase):
    def test_set(self):
        s = vals.Scope()
        self.assertNotIn('a', s)
        s['a'] = builtins_.int_(1)
        self.assertIn('a', s)
        self.assertEqual(s['a'], builtins_.int_(1))
        del s['a']
        self.assertNotIn('a', s)

    def test_as_child(self):
        p = vals.Scope({'a': builtins_.int_(1)})
        s = p.as_child({'a': builtins_.int_(2), 'b': builtins_.int_(3)})
        self.assertEqual(p['a'], builtins_.int_(1))
        self.assertEqual(s['a'], builtins_.int_(2))
        self.assertNotIn('b', p)
        self.assertEqual(s['b'], builtins_.int_(3))
        self.assertDictEqual(
            p.all_vals,
            {'a': builtins_.int_(1)}
        )
        self.assertDictEqual(
            s.all_vals,
            {'a': builtins_.int_(2), 'b': builtins_.int_(3)}
        )


class ArgsTest(TestCase):
    def test_len(self):
        for args, expected in list[tuple[vals.Args, int]]([
            (vals.Args(), 0),
            (vals.Args([vals.Arg(builtins_.int_(1))]), 1),
            (vals.Args([vals.Arg(builtins_.int_(1)),
             vals.Arg(builtins_.int_(2))]), 2),
        ]):
            with self.subTest(args=args, expected=expected):
                self.assertEqual(len(args), expected)

    def test_prepend(self):
        self.assertEqual(
            vals.Args([vals.Arg(builtins_.int_(1))]).prepend(
                vals.Arg(builtins_.int_(2))),
            vals.Args([vals.Arg(builtins_.int_(2)),
                      vals.Arg(builtins_.int_(1))])
        )
