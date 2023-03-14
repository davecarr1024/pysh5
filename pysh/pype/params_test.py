from typing import Optional
from unittest import TestCase
from ..core import errors, tokens
from . import builtins_, params, vals


class ParamTest(TestCase):
    def test_load(self):
        for input, expected in list[tuple[str, params.Param]]([
            (
                'a',
                params.Param('a'),
            ),
        ]):
            with self.subTest(input=input, expected=expected):
                state, actual = params.Param.parse_rule().eval(input)
                self.assertEqual(state, tokens.TokenStream())
                self.assertEqual(actual, expected)


class ParamsTest(TestCase):
    def test_bind_fail(self):
        with self.assertRaises(errors.Error):
            params.Params([]).bind(vals.Scope(), vals.Args(
                [vals.Arg(builtins_.int_(1))]))

    def test_bind(self):
        for params_, args, expected in list[tuple[params.Params, vals.Args, vals.Scope]]([
            (
                params.Params([
                ]),
                vals.Args([
                ]),
                vals.Scope({
                    'a': builtins_.int_(1),
                })
            ),
            (
                params.Params([
                    params.Param('a'),
                ]),
                vals.Args([
                    vals.Arg(builtins_.int_(2)),
                ]),
                vals.Scope({
                    'a': builtins_.int_(2),
                })
            ),
            (
                params.Params([
                    params.Param('b'),
                ]),
                vals.Args([
                    vals.Arg(builtins_.int_(2)),
                ]),
                vals.Scope({
                    'a': builtins_.int_(1),
                    'b': builtins_.int_(2),
                })
            ),
        ]):
            with self.subTest(params_=params_, args=args, expected=expected):
                self.assertEqual(params_.bind(
                    vals.Scope({'a': builtins_.int_(1)}), args), expected)

    def test_tail_fail(self):
        with self.assertRaises(errors.Error):
            params.Params([]).tail

    def test_tail(self):
        for params_, expected in list[tuple[params.Params, params.Params]]([
            (
                params.Params([
                    params.Param('a'),
                ]),
                params.Params([
                ]),
            ),
            (
                params.Params([
                    params.Param('a'),
                    params.Param('b'),
                ]),
                params.Params([
                    params.Param('b'),
                ]),
            ),
        ]):
            with self.subTest(params_=params_, expected=expected):
                self.assertEqual(params_.tail, expected)

    def test_load(self):
        for input, expected in list[tuple[str, Optional[params.Params]]]([
            (
                '',
                None,
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
                '()',
                params.Params(),
            ),
            (
                '(a)',
                params.Params([
                    params.Param('a'),
                ]),
            ),
            (
                '(a, b)',
                params.Params([
                    params.Param('a'),
                    params.Param('b'),
                ]),
            ),
        ]):
            with self.subTest(input=input, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        params.Params.parse_rule().eval(input)
                else:
                    state, actual = params.Params.parse_rule().eval(input)
                    self.assertEqual(state, tokens.TokenStream())
                    self.assertEqual(actual, expected)
