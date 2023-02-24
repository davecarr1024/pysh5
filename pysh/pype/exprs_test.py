from unittest import TestCase
from .exprs import *
from .builtins_ import *


class LiteralTest(TestCase):
    def test_eval(self):
        self.assertEqual(Literal(int_(1)).eval(Scope()), int_(1))


class RefTest(TestCase):
    def test_eval(self):
        for ref, scope, expected in list[tuple[Ref, Scope, Val]]([
            (
                Ref(Ref.Name('a')),
                Scope({
                    'a': int_(1),
                }),
                int_(1),
            ),
            (
                Ref(Ref.Literal(int_(1))),
                Scope({
                }),
                int_(1),
            ),
            (
                Ref(
                    Ref.Literal(
                        Object(
                            Class('c', Scope()),
                            Scope({
                                'a': int_(1)
                            })
                        )
                    ),
                    [
                        Ref.Member('a'),
                    ]
                ),
                Scope(),
                int_(1),
            ),
            (
                Ref(
                    Ref.Literal(
                        int_(1)
                    ),
                    [
                        Ref.Member('__add__'),
                        Ref.Call(Args([Arg(int_(2))])),
                    ]
                ),
                Scope(),
                int_(3),
            ),
        ]):
            with self.subTest(ref=ref, scope=scope, expected=expected):
                self.assertEqual(ref.eval(scope), expected)

    def test_set_name(self):
        scope = Scope()
        Ref(Ref.Name('a')).set(scope, int_(1))
        self.assertEqual(scope['a'], int_(1))

    def test_set_member(self):
        scope = Scope({'o': Object(Class('c', Scope()), Scope())})
        Ref(Ref.Name('o'), [Ref.Member('a')]).set(scope, int_(1))
        self.assertEqual(scope['o']['a'], int_(1))

    def test_set_fail(self):
        for ref in list[Ref]([
            Ref(Ref.Literal(int_(1))),
            Ref(Ref.Name('a'), [Ref.Call(Args([]))]),
        ]):
            with self.subTest(ref=ref):
                with self.assertRaises(Error):
                    ref.set(Scope(), int_(1))

    def test_helper(self):
        for args, expected in list[tuple[tuple[Any, ...], Ref]]([
            (
                ('a',),
                Ref(Ref.Name('a')),
            ),
            (
                (int_(1),),
                Ref(Ref.Literal(int_(1))),
            ),
            (
                ('a', 'b'),
                Ref(Ref.Name('a'), [Ref.Member('b')]),
            ),
            (
                ('a', Args([])),
                Ref(Ref.Name('a'), [Ref.Call(Args([]))]),
            ),
        ]):
            with self.subTest(args=args, expected=expected):
                self.assertEqual(ref(*args), expected)
