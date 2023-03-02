from unittest import TestCase
from . import builtins_, classes, exprs, func, statements, vals


class FuncTest(TestCase):
    def test_call(self):
        for func_, args, expected in list[tuple[func.Func, vals.Args, vals.Val]]([
            (
                func.Func(
                    vals.Params([
                    ]),
                    statements.Block([
                    ]),
                ),
                vals.Args([
                ]),
                builtins_.none,
            ),
            (
                func.Func(
                    vals.Params([
                    ]),
                    statements.Block([
                        statements.Assignment(
                            exprs.ref('a'), exprs.Literal(builtins_.int_(1))),
                    ]),
                ),
                vals.Args([
                ]),
                builtins_.none,
            ),
            (
                func.Func(
                    vals.Params([
                    ]),
                    statements.Block([
                        statements.Return(exprs.Literal(builtins_.int_(1))),
                    ]),
                ),
                vals.Args([
                ]),
                builtins_.int_(1),
            ),
            (
                func.Func(
                    vals.Params([
                        vals.Param('a'),
                    ]),
                    statements.Block([
                        statements.Return(exprs.Ref(exprs.Ref.Name('a'))),
                    ]),
                ),
                vals.Args([
                    vals.Arg(builtins_.int_(1)),
                ]),
                builtins_.int_(1),
            ),
        ]):
            with self.subTest(func_=func_, args=args, expected=expected):
                self.assertEqual(func_(vals.Scope(), args), expected)


class MethodTest(TestCase):
    def test_call(self):
        for method, object_, args, expected in list[tuple[func.Method, vals.Val, vals.Args, vals.Val]]([
            (
                func.Method(
                    vals.Params([
                        vals.Param('self'),
                    ]),
                    statements.Block([
                        statements.Return(exprs.Ref(exprs.Ref.Name(
                            'self'), [exprs.Ref.Member('a')])),
                    ])
                ),
                classes.Object(
                    classes.Class('c', vals.Scope()),
                    vals.Scope({
                        'a': builtins_.int_(1),
                    })
                ),
                vals.Args([]),
                builtins_.int_(1),
            ),
        ]):
            with self.subTest(method=method, object_=object_, args=args, expected=expected):
                self.assertEqual(method.bind(object_)(
                    vals.Scope(), args), expected)
