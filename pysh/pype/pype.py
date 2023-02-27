from typing import OrderedDict
from ..errors import *
from .. import lexer, parser
from .statements import *
from .builtins_ import *


def load(input: str) -> Statement:
    tokens = lexer.Lexer(OrderedDict(

    ))(input)

    _, statement = parser.Parser[Statement](
        'statement',
        parser.Scope[Statement]({
            'statement': Statement.load,
        })
    )(tokens)
    return statement


def eval(input: str, scope: Scope | None = None) -> Val:
    result = load(input).eval(scope or Scope())
    if result.has_return_value():
        return result.return_value()
    return none
