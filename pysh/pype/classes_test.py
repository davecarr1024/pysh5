from unittest import TestCase
from . import builtins_, classes, exprs, func, params, statements, vals


class ClassTest(TestCase):
    def test_class_member(self):
        c = classes.Class(
            'c',
            vals.Scope({
                'a': builtins_.int_(1),
            })
        )
        self.assertEqual(c['a'], builtins_.int_(1))
        o = c.instantiate()
        self.assertEqual(o['a'], builtins_.int_(1))
        o['a'] = builtins_.int_(2)
        self.assertEqual(c['a'], builtins_.int_(1))
        self.assertEqual(o['a'], builtins_.int_(2))

    def test_init(self):
        c = classes.Class(
            'c',
            vals.Scope({
                '__init__': func.Method(
                    'f',
                    params.Params([params.Param('self')]),
                    statements.Block([
                        statements.Assignment(exprs.ref('self', 'a'),
                                              exprs.ref(builtins_.int_(1))),
                    ])
                )
            })
        )
        o = c(vals.Scope(), vals.Args([]))
        self.assertEqual(o['a'], builtins_.int_(1))
