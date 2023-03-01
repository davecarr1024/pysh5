from typing import Type
from . import regex, lexer, parser, tokens


def load_regex(input: str) -> regex.Regex:
    operators = '()|[-]^*+?!\\'
    lexer_ = lexer.Lexer([
        lexer.Rule(operator, regex.literal(operator))
        for operator in operators
    ]+[
        lexer.Rule('literal', regex.Any())
    ])
    tokens_ = lexer_(input)

    def load_and(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
        state, _ = state.pop('(')
        state, rules = parser.OneOrMore[regex.Regex](load_rule)(state, scope)
        state, _ = state.pop(')')
        if len(rules) == 1:
            return state, rules[0]
        return state, regex.And(rules)

    def load_or(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
        def load_tail(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
            state, _ = state.pop('|')
            return load_rule(state, scope)

        state, _ = state.pop('(')
        state, head = load_rule(state, scope)
        state, tails = parser.OneOrMore[regex.Regex](load_tail)(state, scope)
        state, _ = state.pop(')')
        return state, regex.Or([head] + list(tails))

    load_literal = parser.Literal[regex.Regex](
        'literal', lambda token: regex.literal(token.val))

    def load_postfix(operator: str, type: Type[regex.UnaryRegex]) -> parser.Rule[regex.Regex]:
        def inner(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
            state, rule = load_operand(state, scope)
            state, _ = state.pop(operator)
            return state, type(rule)
        return inner

    load_zero_or_more = load_postfix('*', regex.ZeroOrMore)
    load_one_or_more = load_postfix('+', regex.OneOrMore)
    load_zero_or_one = load_postfix('?', regex.ZeroOrOne)
    load_until_empty = load_postfix('!', regex.UntilEmpty)

    load_operand = parser.Or[regex.Regex]([load_or, load_and, load_literal])

    load_operation = parser.Or[regex.Regex](
        [load_zero_or_more, load_one_or_more, load_zero_or_one, load_until_empty])

    load_rule = parser.Or[regex.Regex]([load_operation, load_operand])

    _, rules = parser.UntilEmpty[regex.Regex](
        load_rule)(tokens_, parser.Scope[regex.Regex]())
    if len(rules) == 1:
        return rules[0]
    else:
        return regex.And(rules)
