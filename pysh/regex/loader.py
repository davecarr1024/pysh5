from typing import Type
from .. import parser
from .. import lexer
from ..lexer.tokens import *
from .rules import *


def load(input: str) -> Rule:
    def load_and(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
        def load_body(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
            state, rules = parser.OneOrMore[Rule](load_rule)(state, scope)
            if len(rules) == 1:
                return state, rules[0]
            return state, And(rules)
        return parser.format('(', load_body, ')')(state, scope)

    def load_or(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
        state, head = load_operand(state, scope)
        load_tail = parser.format('|', load_operand)
        state, tail = parser.OneOrMore[Rule](load_tail)(state, scope)
        return state, Or([head]+list(tail))

    def load_unary(rule: Type[UnaryRule]) -> parser.Rule[Rule]:
        def inner(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
            state, result = load_operand(state, scope)
            return state, rule(result)
        return inner

    def load_postfix(operator: str, rule: Type[UnaryRule]) -> parser.Rule[Rule]:
        return parser.format(load_unary(rule), operator)

    load_zero_or_more = load_postfix('*', ZeroOrMore)
    load_one_or_more = load_postfix('+', OneOrMore)
    load_zero_or_one = load_postfix('?', ZeroOrOne)
    load_until_empty = load_postfix('!', UntilEmpty)
    load_not = parser.format('^', load_unary(Not))

    def load_class(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
        def token_val(state: TokenStream, scope: parser.Scope[str]) -> parser.StateAndResult[str]:
            return state.tail(), state.head().val
        state, (start, end) = parser.multiple_result_format(
            '[',
            token_val,
            '-',
            token_val,
            ']',
        )(state, parser.Scope[str]())
        return state, Class(start, end)

    def load_special(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
        state = state.pop('\\')
        return state.tail(), Literal(Char(state.head().val))

    load_literal = parser.Literal[Rule](
        'literal', lambda token: Literal(Char(token.val)))

    load_operand = parser.Or[Rule]([
        load_literal,
        load_class,
        load_and,
        load_special,
    ])

    load_rule = parser.Or[Rule]([
        load_or,
        load_not,
        load_zero_or_more,
        load_one_or_more,
        load_zero_or_one,
        load_until_empty,
        load_operand,
    ])

    operators = '()[-]^|+*?!\\'
    tokens = lexer.Lexer([
        lexer.Rule.literal(operator)
        for operator in operators
    ] + [
        lexer.Rule('literal', regex.Any()),
    ])(input)

    _, rules = parser.UntilEmpty[Rule](load_rule)(tokens, parser.Scope[Rule]())
    if len(rules) == 1:
        return rules[0]
    return And(rules)
