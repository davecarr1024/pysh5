from unittest import TestCase
from .classes import *
from .func import *


class ClassTest(TestCase):
    def test_class_member(self):
        c = Class(
            'c',
            Scope({
                'a': int_(1),
            })
        )
        self.assertEqual(c['a'], int_(1))
        o = c.instantiate()
        self.assertEqual(o['a'], int_(1))
        o['a'] = int_(2)
        self.assertEqual(c['a'], int_(1))
        self.assertEqual(o['a'], int_(2))

    def test_init(self):
        c = Class(
            'c',
            Scope({
                '__init__': Method(
                    Params([Param('self')]),
                    Block([
                        Assignment(ref('self', 'a'), Literal(int_(1))),
                    ])
                )
            })
        )
        o = c(Scope(), Args([]))
        self.assertEqual(o['a'], int_(1))
