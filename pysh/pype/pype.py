from typing import Optional, Sequence
from . import builtins_, statements, vals


def load(input: str) -> statements.Statement:
    def load(statements_: Sequence[statements.Statement]) -> statements.Statement:
        if len(statements_) == 1:
            return statements_[0]
        else:
            return statements.Block(statements_)

    _, statements_ = statements.Statement.parser_(
    ).until_empty().convert(load).eval(input)
    return statements_


def eval(input: str, scope: Optional[vals.Scope] = None) -> vals.Val:
    statement = load(input)
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
