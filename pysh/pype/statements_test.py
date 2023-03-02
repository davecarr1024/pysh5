from unittest import TestCase
from . import builtins_, exprs, statements, vals


class AssignmentTest(TestCase):
    def test_eval(self):
        scope = vals.Scope()
        self.assertEqual(
            statements.Assignment(
                exprs.Ref(exprs.Ref.Name('a')),
                exprs.Literal(builtins_.int_(1)),
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
                statements.Return(exprs.Literal(builtins_.int_(1))),
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
                        exprs.ref('a'), exprs.Literal(builtins_.int_(1))),
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
                    statements.Return(exprs.Literal(builtins_.int_(1)),)
                ]),
                statements.Statement.Result.for_return(builtins_.int_(1)),
            ),
            (
                statements.Block([
                    statements.Assignment(
                        exprs.ref('a'), exprs.Literal(builtins_.int_(1))),
                    statements.Return(exprs.ref('a')),
                ]),
                statements.Statement.Result.for_return(builtins_.int_(1)),
            ),
        ]):
            with self.subTest(block=block, expected=expected):
                self.assertEqual(block.eval(vals.Scope()), expected)
