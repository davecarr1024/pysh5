from typing import OrderedDict, Type
from .. import parser
from .. import lexer
from ..lexer.tokens import *
from .rules import *


def load(input: str) -> Rule:
    def load_and(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
        state = state.pop('(')
        state, rules = parser.OneOrMore[Rule](load_rule)(state, scope)
        state = state.pop(')')
        if len(rules) == 1:
            return state, rules[0]
        return state, And(rules)

    def load_or(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
        state, head = load_operand(state, scope)

        def load_tail(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
            state = state.pop('|')
            return load_operand(state, scope)

        state, tail = parser.OneOrMore[Rule](load_tail)(state, scope)
        return state, Or([head]+list(tail))

    def load_postfix(operator: str, rule: Type[UnaryRule]) -> parser.Rule[Rule]:
        def inner(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
            state, result = load_operand(state, scope)
            state = state.pop(operator)
            return state, rule(result)
        return inner

    load_zero_or_more = load_postfix('*', ZeroOrMore)
    load_one_or_more = load_postfix('+', OneOrMore)
    load_zero_or_one = load_postfix('?', ZeroOrOne)
    load_until_empty = load_postfix('!', UntilEmpty)

    def load_not(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
        state = state.pop('^')
        state, result = load_operand(state, scope)
        return state, Not(result)

    def load_class(state: TokenStream, scope: parser.Scope[Rule]) -> parser.StateAndResult[Rule]:
        state = state.pop('[')
        state, start = state.pop_val('literal')
        state = state.pop('-')
        state, end = state.pop_val('literal')
        state = state.pop(']')
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
    tokens = lexer.Lexer(
        OrderedDict[str, Rule](
            OrderedDict[str, Rule]({
                operator: Literal(Char(operator)) for operator in operators
            }) | OrderedDict[str, Rule](
                literal=Any(),
            )
        )
    )(input)

    _, rules = parser.UntilEmpty[Rule](load_rule)(tokens, parser.Scope[Rule]())
    if len(rules) == 1:
        return rules[0]
    return And(rules)
