from unittest import TestCase
from .statements import *
from .builtins_ import *


class AssignmentTest(TestCase):
    def test_eval(self):
        scope = Scope()
        self.assertEqual(
            Assignment(
                Ref(Ref.Name('a')),
                Literal(int_(1)),
            ).eval(scope),
            Statement.Result()
        )
        self.assertEqual(scope['a'], int_(1))


class ReturnTest(TestCase):
    def test_eval(self):
        for return_, expected in list[tuple[Return, Statement.Result]]([
            (
                Return(),
                Statement.Result.for_return(),
            ),
            (
                Return(Literal(int_(1))),
                Statement.Result.for_return(int_(1)),
            ),
        ]):
            with self.subTest(return_=return_, expected=expected):
                self.assertEqual(return_.eval(Scope()), expected)


class BlockTest(TestCase):
    def test_eval(self):
        for block, expected in list[tuple[Block, Statement.Result]]([
            (
                Block([
                ]),
                Statement.Result(),
            ),
            (
                Block([
                    Assignment(ref('a'), Literal(int_(1))),
                ]),
                Statement.Result(),
            ),
            (
                Block([
                    Return()
                ]),
                Statement.Result.for_return(),
            ),
            (
                Block([
                    Return(Literal(int_(1)),)
                ]),
                Statement.Result.for_return(int_(1)),
            ),
            (
                Block([
                    Assignment(ref('a'), Literal(int_(1))),
                    Return(ref('a')),
                ]),
                Statement.Result.for_return(int_(1)),
            ),
        ]):
            with self.subTest(block=block, expected=expected):
                self.assertEqual(block.eval(Scope()), expected)
