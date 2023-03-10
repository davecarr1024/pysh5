from typing import Optional
from unittest import TestCase
from . import builtins_, exprs, statements, vals
from ..core import errors, parser, tokens


class AssignmentTest(TestCase):
    def test_eval(self):
        scope = vals.Scope()
        self.assertEqual(
            statements.Assignment(
                exprs.Ref(exprs.Ref.Name('a')),
                exprs.ref(builtins_.int_(1)),
            ).eval(scope),
            statements.Statement.Result()
        )
        self.assertEqual(scope['a'], builtins_.int_(1))


class ReturnTest(TestCase):
    def test_eval(self):
        for return_, expected in list[tuple[statements.Return, statements.Statement.Result]]([
            (
                statements.Return(),
                statements.Statement.Result.for_return(),
            ),
            (
                statements.Return(exprs.ref(builtins_.int_(1))),
                statements.Statement.Result.for_return(builtins_.int_(1)),
            ),
        ]):
            with self.subTest(return_=return_, expected=expected):
                self.assertEqual(return_.eval(vals.Scope()), expected)


class BlockTest(TestCase):
    def test_eval(self):
        for block, expected in list[tuple[statements.Block, statements.Statement.Result]]([
            (
                statements.Block([
                ]),
                statements.Statement.Result(),
            ),
            (
                statements.Block([
                    statements.Assignment(
                        exprs.ref('a'), exprs.ref(builtins_.int_(1))),
                ]),
                statements.Statement.Result(),
            ),
            (
                statements.Block([
                    statements.Return()
                ]),
                statements.Statement.Result.for_return(),
            ),
            (
                statements.Block([
                    statements.Return(exprs.ref(builtins_.int_(1)),)
                ]),
                statements.Statement.Result.for_return(builtins_.int_(1)),
            ),
            (
                statements.Block([
                    statements.Assignment(
                        exprs.ref('a'), exprs.ref(builtins_.int_(1))),
                    statements.Return(exprs.ref('a')),
                ]),
                statements.Statement.Result.for_return(builtins_.int_(1)),
            ),
        ]):
            with self.subTest(block=block, expected=expected):
                self.assertEqual(block.eval(vals.Scope()), expected)


class StatementTest(TestCase):
    def test_load(self):
        for state, expected in list[tuple[tokens.TokenStream | str, Optional[statements.Statement]]]([
            (
                tokens.TokenStream([]),
                None,
            ),
            (
                tokens.TokenStream([
                    tokens.Token('{', '{'),
                    tokens.Token('}', '}'),
                ]),
                statements.Block(),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token(';', ';'),
                ]),
                statements.ExprStatement(
                    exprs.ref(
                        builtins_.int_(1),
                    )
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                ]),
                None,
            ),
            (
                tokens.TokenStream([
                    tokens.Token(';', ';'),
                ]),
                None,
            ),
            (
                tokens.TokenStream([
                    tokens.Token('id', 'a'),
                    tokens.Token('=', '='),
                    tokens.Token('int', '1'),
                    tokens.Token(';', ';'),
                ]),
                statements.Assignment(
                    exprs.ref('a'),
                    exprs.ref(
                        builtins_.int_(1)
                    )
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('return', 'return'),
                    tokens.Token(';', ';'),
                ]),
                statements.Return(),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('return', 'return'),
                    tokens.Token('int', '1'),
                    tokens.Token(';', ';'),
                ]),
                statements.Return(
                    exprs.ref(
                        builtins_.int_(1)
                    )
                ),
            ),
            (
                '',
                None,
            ),
            (
                '1;',
                statements.ExprStatement(
                    exprs.ref(
                        builtins_.int_(1)
                    )
                ),
            ),
            (
                'return;',
                statements.Return(),
            ),
            (
                'return 1;',
                statements.Return(
                    exprs.ref(
                        builtins_.int_(1)
                    )
                ),
            ),
            (
                'a = 1;',
                statements.Assignment(
                    exprs.ref('a'),
                    exprs.ref(builtins_.int_(1)),
                ),
            ),
            (
                '{ }',
                statements.Block(),
            ),
            (
                '{ 1; }',
                statements.Block([
                    statements.ExprStatement(
                        exprs.ref(builtins_.int_(1))
                    )
                ]),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        statements.Statement.parser_()(state)
                else:
                    state, result = statements.Statement.parser_()(state)
                    self.assertEqual(state, tokens.TokenStream())
                    self.assertEqual(result, expected,
                                     f'{result} != {expected}')
