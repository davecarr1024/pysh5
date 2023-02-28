from .. import lexer, regex

INT = lexer.Rule('int', regex.load(''))

LEXER = lexer.Lexer([INT])
