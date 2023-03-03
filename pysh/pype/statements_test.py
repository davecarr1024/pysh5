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
        for state, expected in list[tuple[tokens.TokenStream, Optional[parser.StateAndResult[statements.Statement]]]]([
            (
                tokens.TokenStream([]),
                (
                    tokens.TokenStream([]),
                    statements.Block(),
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('{', '{'),
                    tokens.Token('}', '}'),
                ]),
                (
                    tokens.TokenStream([]),
                    statements.Block(),
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('int', '1'),
                    tokens.Token(';', ';'),
                ]),
                (
                    tokens.TokenStream([]),
                    statements.ExprStatement(
                        exprs.ref(
                            builtins_.int_(1),
                        )
                    ),
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
                (
                    tokens.TokenStream([]),
                    statements.Assignment(
                        exprs.ref('a'),
                        exprs.ref(
                            builtins_.int_(1)
                        )
                    ),
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('return', 'return'),
                    tokens.Token(';', ';'),
                ]),
                (
                    tokens.TokenStream([]),
                    statements.Return(),
                ),
            ),
            (
                tokens.TokenStream([
                    tokens.Token('return', 'return'),
                    tokens.Token('int', '1'),
                    tokens.Token(';', ';'),
                ]),
                (
                    tokens.TokenStream([]),
                    statements.Return(
                        exprs.ref(
                            builtins_.int_(1)
                        )
                    ),
                ),
            ),
        ]):
            with self.subTest(state=state, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        statements.Statement.parser_()(state)
                else:
                    self.assertEqual(
                        statements.Statement.parser_()(state), expected)
