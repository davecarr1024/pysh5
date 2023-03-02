from typing import Any
from unittest import TestCase
from . import builtins_, classes, exprs, vals
from ..core import errors


class LiteralTest(TestCase):
    def test_eval(self):
        self.assertEqual(exprs.Literal(builtins_.int_(1)).eval(
            vals.Scope()), builtins_.int_(1))


class RefTest(TestCase):
    def test_eval(self):
        for ref, scope, expected in list[tuple[exprs.Ref, vals.Scope, vals.Val]]([
            (
                exprs.Ref(exprs.Ref.Name('a')),
                vals.Scope({
                    'a': builtins_.int_(1),
                }),
                builtins_.int_(1),
            ),
            (
                exprs.Ref(exprs.Ref.Literal(builtins_.int_(1))),
                vals.Scope({
                }),
                builtins_.int_(1),
            ),
            (
                exprs.Ref(
                    exprs.Ref.Literal(
                        classes.Object(
                            classes.Class('c', vals.Scope()),
                            vals.Scope({
                                'a': builtins_.int_(1)
                            })
                        )
                    ),
                    [
                        exprs.Ref.Member('a'),
                    ]
                ),
                vals.Scope(),
                builtins_.int_(1),
            ),
            (
                exprs.Ref(
                    exprs.Ref.Literal(
                        builtins_.int_(1)
                    ),
                    [
                        exprs.Ref.Member('__add__'),
                        exprs.Ref.Call(
                            vals.Args([vals.Arg(builtins_.int_(2))])),
                    ]
                ),
                vals.Scope(),
                builtins_.int_(3),
            ),
        ]):
            with self.subTest(ref=ref, scope=scope, expected=expected):
                self.assertEqual(ref.eval(scope), expected)

    def test_set_name(self):
        scope = vals.Scope()
        exprs.Ref(exprs.Ref.Name('a')).set(scope, builtins_.int_(1))
        self.assertEqual(scope['a'], builtins_.int_(1))

    def test_set_member(self):
        scope = vals.Scope({'o': classes.Object(
            classes.Class('c', vals.Scope()), vals.Scope())})
        exprs.Ref(exprs.Ref.Name('o'), [exprs.Ref.Member('a')]).set(
            scope, builtins_.int_(1))
        self.assertEqual(scope['o']['a'], builtins_.int_(1))

    def test_set_fail(self):
        for ref in list[exprs.Ref]([
            exprs.Ref(exprs.Ref.Literal(builtins_.int_(1))),
            exprs.Ref(exprs.Ref.Name('a'), [exprs.Ref.Call(vals.Args([]))]),
        ]):
            with self.subTest(ref=ref):
                with self.assertRaises(errors.Error):
                    ref.set(vals.Scope(), builtins_.int_(1))

    def test_helper(self):
        for args, expected in list[tuple[tuple[Any, ...], exprs.Ref]]([
            (
                ('a',),
                exprs.Ref(exprs.Ref.Name('a')),
            ),
            (
                (builtins_.int_(1),),
                exprs.Ref(exprs.Ref.Literal(builtins_.int_(1))),
            ),
            (
                ('a', 'b'),
                exprs.Ref(exprs.Ref.Name('a'), [exprs.Ref.Member('b')]),
            ),
            (
                ('a', vals.Args([])),
                exprs.Ref(exprs.Ref.Name('a'), [
                          exprs.Ref.Call(vals.Args([]))]),
            ),
        ]):
            with self.subTest(args=args, expected=expected):
                self.assertEqual(exprs.ref(*args), expected)
