from ..core import lexer, regex

whitespace = lexer.Rule('ws', regex.load('~(\\w+)'))
id = lexer.Rule('id', regex.load(
    '([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*'))
lexer_ = lexer.Lexer([whitespace, id])
