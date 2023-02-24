from unittest import TestCase
from .func import *


class FuncTest(TestCase):
    def test_call(self):
        for func, args, expected in list[tuple[Func, Args, Val]]([
            (
                Func(
                    Params([
                    ]),
                    Block([
                    ]),
                ),
                Args([
                ]),
                none,
            ),
            (
                Func(
                    Params([
                    ]),
                    Block([
                        Assignment(ref('a'), Literal(int_(1))),
                    ]),
                ),
                Args([
                ]),
                none,
            ),
            (
                Func(
                    Params([
                    ]),
                    Block([
                        Return(Literal(int_(1))),
                    ]),
                ),
                Args([
                ]),
                int_(1),
            ),
            (
                Func(
                    Params([
                        Param('a'),
                    ]),
                    Block([
                        Return(Ref(Ref.Name('a'))),
                    ]),
                ),
                Args([
                    Arg(int_(1)),
                ]),
                int_(1),
            ),
        ]):
            with self.subTest(func=func, args=args, expected=expected):
                self.assertEqual(func(Scope(), args), expected)


class MethodTest(TestCase):
    def test_call(self):
        for method, object_, args, expected in list[tuple[Method, Val, Args, Val]]([
            (
                Method(
                    Params([
                        Param('self'),
                    ]),
                    Block([
                        Return(Ref(Ref.Name('self'), [Ref.Member('a')])),
                    ])
                ),
                Object(
                    Class('c', Scope()),
                    Scope({
                        'a': int_(1),
                    })
                ),
                Args([]),
                int_(1),
            ),
        ]):
            with self.subTest(method=method, object_=object_, args=args, expected=expected):
                self.assertEqual(method.bind(object_)(Scope(), args), expected)
