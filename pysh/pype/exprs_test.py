from typing import Any, Optional
from unittest import TestCase
from . import builtins_, classes, exprs, vals
from ..core import errors, parser, tokens


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
                            exprs.Args([exprs.Arg(exprs.Literal(builtins_.int_(2)))])),
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
            exprs.Ref(exprs.Ref.Name('a'), [exprs.Ref.Call(exprs.Args([]))]),
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
                ('a', exprs.Args([])),
                exprs.Ref(exprs.Ref.Name('a'), [
                          exprs.Ref.Call(exprs.Args([]))]),
            ),
        ]):
            with self.subTest(args=args, expected=expected):
                self.assertEqual(exprs.ref(*args), expected)


class ArgTest(TestCase):
    def test_eval(self):
        for arg, scope, expected in list[tuple[exprs.Arg, vals.Scope, Optional[vals.Arg]]]([
            (
                exprs.Arg(
                    exprs.Literal(
                        builtins_.int_(1)
                    )
                ),
                vals.Scope(),
                vals.Arg(
                    builtins_.int_(1)
                )
            ),
            (
                exprs.Arg(
                    exprs.ref('a')
                ),
                vals.Scope({
                    'a': builtins_.int_(1),
                }),
                vals.Arg(
                    builtins_.int_(1)
                )
            ),
            (
                exprs.Arg(
                    exprs.ref('a')
                ),
                vals.Scope(),
                None
            ),
        ]):
            with self.subTest(arg=arg, scope=scope, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        arg.eval(scope)
                else:
                    self.assertEqual(arg.eval(scope), expected)

    def test_load(self):
        for state, expected in list[tuple[tokens.TokenStream, parser.StateAndResult[exprs.Arg]]]([
            (
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                (
                    tokens.TokenStream([]),
                    exprs.Arg(exprs.Literal(builtins_.int_(1))),
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token('r', 'a'),
                ]),
                (
                    tokens.TokenStream([
                        tokens.Token('r', 'a'),
                    ]),
                    exprs.Arg(exprs.Literal(builtins_.int_(1))),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                self.assertEqual(exprs.Arg.loader(exprs.Expr.parser_().rules)(
                    state, parser.Scope[exprs.Arg]()), expected)


class ArgsTest(TestCase):
    def test_eval(self):
        for args, scope, expected in list[tuple[exprs.Args, vals.Scope, Optional[vals.Args]]]([
            (
                exprs.Args(),
                vals.Scope(),
                vals.Args(),
            ),
            (
                exprs.Args([
                    exprs.Arg(exprs.Literal(builtins_.int_(1))),
                    exprs.Arg(exprs.ref('a')),
                ]),
                vals.Scope({
                    'a': builtins_.int_(2),
                }),
                vals.Args([
                    vals.Arg(builtins_.int_(1)),
                    vals.Arg(builtins_.int_(2)),
                ]),
            ),
            (
                exprs.Args([
                    exprs.Arg(exprs.ref('a')),
                ]),
                vals.Scope(),
                None,
            ),
        ]):
            with self.subTest(args=args, scope=scope, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        args.eval(scope)
                else:
                    self.assertEqual(args.eval(scope), expected)

    def test_load(self):
        for state, expected in list[tuple[tokens.TokenStream, Optional[parser.StateAndResult[exprs.Args]]]]([
            (
                tokens.TokenStream([
                    tokens.Token('(', '('),
                    tokens.Token(')', ')'),
                ]),
                (
                    tokens.TokenStream([]),
                    exprs.Args([]),
                )
            ),
            (
                tokens.TokenStream([
                    tokens.Token('(', '('),
                    tokens.Token('id', 'a'),
                    tokens.Token(')', ')'),
                ]),
                (
                    tokens.TokenStream([]),
                    exprs.Args([
                        exprs.Arg(exprs.ref('a')),
                    ]),
                )
            ),
            (
                tokens.TokenStream([
                    tokens.Token('(', '('),
                    tokens.Token('id', 'a'),
                    tokens.Token(',', ','),
                    tokens.Token('id', 'b'),
                    tokens.Token(')', ')'),
                ]),
                (
                    tokens.TokenStream([]),
                    exprs.Args([
                        exprs.Arg(exprs.ref('a')),
                        exprs.Arg(exprs.ref('b')),
                    ]),
                )
            ),
            (
                tokens.TokenStream([
                    tokens.Token('(', '('),
                ]),
                None,
            ),
            (
                tokens.TokenStream([
                    tokens.Token('(', '('),
                    tokens.Token('id', 'a'),
                ]),
                None,
            ),
            (
                tokens.TokenStream([
                    tokens.Token('(', '('),
                    tokens.Token('id', 'a'),
                    tokens.Token(',', ','),
                ]),
                None,
            ),
            (
                tokens.TokenStream([
                    tokens.Token('(', '('),
                    tokens.Token('id', 'a'),
                    tokens.Token(',', ','),
                    tokens.Token(')', ')'),
                ]),
                None,
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        exprs.Args.loader(exprs.Expr.parser_().rules)(
                            state, parser.Scope[exprs.Args]())
                else:
                    self.assertEqual(
                        exprs.Args.loader(exprs.Expr.parser_().rules)(
                            state, parser.Scope[exprs.Args]()),
                        expected
                    )
