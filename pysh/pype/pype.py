from typing import Optional
from . import builtins_, statements, vals
from ..core import parser


def eval(input: str, scope: Optional[vals.Scope] = None) -> vals.Val:
    _, statement = statements.Statement.parser_()(input)
    scope = scope or vals.Scope()
    if isinstance(statement, statements.Block) and statement.statements:
        for s in statement.statements[:-1]:
            s.eval(scope)
        last_statement = statement.statements[-1]
    else:
        last_statement = statement
    if isinstance(last_statement, statements.ExprStatement):
        return last_statement.val.eval(scope)
    else:
        last_statement.eval(scope)
        return builtins_.none
