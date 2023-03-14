from typing import Any, Optional
from unittest import TestCase
from . import builtins_, classes, exprs, vals
from ..core import errors,  tokens

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    __import__('sys').modules['unittest.util']._MAX_LENGTH = 999999999

_ref = exprs.ref
_int = builtins_.int_


def _arg(val: vals.Val | str | exprs.Expr) -> exprs.Arg:
    if isinstance(val, vals.Val):
        return exprs.Arg(_ref(val))
    elif isinstance(val, str):
        return exprs.Arg(_ref(val))
    else:
        return exprs.Arg(val)


def _args(*vals: vals.Val | str | exprs.Expr) -> exprs.Args:
    return exprs.Args([_arg(val) for val in vals])


class ExprTest(TestCase):
    def test_load(self):
        for input, expected in list[tuple[str, Optional[exprs.Expr]]]([
            (
                '1',
                _ref(_int(1)),
            ),
            (
                'a',
                _ref('a'),
            ),
            (
                'a.b',
                _ref('a', 'b'),
            ),
            (
                'a()',
                _ref('a', _args()),
            ),
            (
                'a(b)',
                _ref('a', _args('b')),
            ),
            (
                'a(1)',
                _ref('a', _args(_int(1))),
            ),
            (
                '1(a)',
                _ref(_int(1), _args('a')),
            ),
            (
                'a(b, c)',
                _ref('a', _args('b', 'c')),
            ),
            (
                'a.b(c, d)',
                _ref('a', 'b', _args('c', 'd')),
            ),
            (
                'a(b, c).d',
                _ref('a', _args('b', 'c'), 'd'),
            ),
        ]):
            with self.subTest(input=input, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        exprs.Expr.parser_()(input)
                else:
                    state, actual = exprs.Expr.parser_()(input)
                    self.assertEqual(state, tokens.TokenStream())
                    self.assertEqual(actual, expected,
                                     f'{actual} != {expected}')


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
                            exprs.Args([exprs.Arg(exprs.ref(builtins_.int_(2)))])),
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
                    exprs.ref(
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
        for input, expected in list[tuple[str, exprs.Arg]]([
            (
                '1',
                exprs.Arg(exprs.ref(builtins_.int_(1))),
            ),
            (
                'a',
                exprs.Arg(exprs.ref('a')),
            ),
        ]):
            with self.subTest(input=input, expected=expected):
                state, expr = exprs.Arg.parse_rule(
                    exprs.Expr.parser_().scope).eval(input)
                self.assertEqual(state, tokens.TokenStream())
                self.assertEqual(expr, expected)


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
                    exprs.Arg(exprs.ref(builtins_.int_(1))),
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

    def test_eq(self):
        for lhs, rhs in list[tuple[exprs.Args, exprs.Args]]([
            (
                exprs.Args([]),
                exprs.Args([]),
            ),
            (
                exprs.Args([
                    exprs.Arg(exprs.ref('a')),
                ]),
                exprs.Args([
                    exprs.Arg(exprs.ref('a')),
                ]),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs):
                self.assertEqual(lhs, rhs)

    def test_neq(self):
        for lhs, rhs in list[tuple[exprs.Args, exprs.Args]]([
            (
                exprs.Args([]),
                exprs.Args([
                    exprs.Arg(exprs.ref('a')),
                ]),
            ),
            (
                exprs.Args([
                    exprs.Arg(exprs.ref('a')),
                ]),
                exprs.Args([]),
            ),
            (
                exprs.Args([
                    exprs.Arg(exprs.ref('a')),
                ]),
                exprs.Args([
                    exprs.Arg(exprs.ref('b')),
                ]),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs):
                self.assertNotEqual(lhs, rhs)

    def test_load(self):
        for input, expected in list[tuple[str, Optional[exprs.Args]]]([
            (
                '()',
                exprs.Args(),
            ),
            (
                '(a)',
                exprs.Args([
                    exprs.Arg(
                        exprs.ref('a')
                    ),
                ]),
            ),
            (
                '(a, b)',
                exprs.Args([
                    exprs.Arg(
                        exprs.ref('a')
                    ),
                    exprs.Arg(
                        exprs.ref('b')
                    ),
                ]),
            ),
            (
                '(a, b, c)',
                exprs.Args([
                    exprs.Arg(
                        exprs.ref('a')
                    ),
                    exprs.Arg(
                        exprs.ref('b')
                    ),
                    exprs.Arg(
                        exprs.ref('c')
                    ),
                ]),
            ),
            (
                '(',
                None,
            ),
            (
                '(a',
                None,
            ),
            (
                '(a,',
                None,
            ),
            (
                '(a,)',
                None,
            ),
        ]):
            with self.subTest(input=input, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        exprs.Args.parse_rule(
                            exprs.Expr.parser_().scope).eval(input)
                else:
                    state, actual = exprs.Args.parse_rule(
                        exprs.Expr.parser_().scope).eval(input)
                    self.assertEqual(state, tokens.TokenStream())
                    self.assertEqual(actual, expected,
                                     f'{actual} != {expected}')
