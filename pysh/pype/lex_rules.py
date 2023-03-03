from ..core import lexer, loader

whitespace = lexer.Rule('ws', loader.load_regex('~(\\w+)'))
id = lexer.Rule('id', loader.load_regex(
    '([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*'))
lexer_ = lexer.Lexer([whitespace, id])
