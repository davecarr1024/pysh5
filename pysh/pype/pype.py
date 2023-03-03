from typing import Optional
from . import builtins_, statements, vals
from ..core import errors, lexer, loader, parser, tokens


def eval(input: str, scope: Optional[vals.Scope] = None) -> vals.Val:
    lexer_ = lexer.Lexer.literals(list(';={}(),') + ['return']) | lexer.Lexer([
        lexer.Rule('id', loader.load_regex(
            '([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*')),
        lexer.Rule('int', loader.load_regex('(\\-)?[0-9]+')),
        lexer.Rule('ws', loader.load_regex('~(\\w+)')),
    ])
    tokens_ = lexer_(input)
    _, statements_ = parser.UntilEmpty[statements.Statement](
        statements.Statement.parser_())(tokens_, statements.Statement.parser_().scope)
    if not statements_:
        return builtins_.none
    scope = scope or vals.Scope()
    for statement in statements_[:-1]:
        statement.eval(scope)
    last_statement = statements_[-1]
    if isinstance(last_statement, statements.ExprStatement):
        return last_statement.val.eval(scope)
    else:
        last_statement.eval(scope)
        return builtins_.none
