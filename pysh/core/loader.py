from typing import Type
from . import regex, lexer, parser, tokens


def load_regex(input: str) -> regex.Regex:
    operators = '()|[-]^*+?!\\~'
    lexer_ = lexer.Lexer([
        lexer.Rule(operator, regex.literal(operator))
        for operator in operators
    ]+[
        lexer.Rule('literal', regex.Any())
    ])
    tokens_ = lexer_(input)

    def load_and(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
        state, _ = state.pop('(')
        state, rules = parser.OneOrMore[regex.Regex](load_regex)(state, scope)
        state, _ = state.pop(')')
        if len(rules) == 1:
            return state, rules[0]
        return state, regex.And(rules)

    def load_or(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
        def load_tail(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
            state, _ = state.pop('|')
            return load_regex(state, scope)

        state, _ = state.pop('(')
        state, head = load_regex(state, scope)
        state, tails = parser.OneOrMore[regex.Regex](load_tail)(state, scope)
        state, _ = state.pop(')')
        return state, regex.Or([head] + list(tails))

    load_literal = parser.Literal[regex.Regex](
        'literal', lambda token: regex.literal(token.val))

    def load_postfix(operator: str, type: Type[regex.UnaryRegex]) -> parser.Rule[regex.Regex]:
        def inner(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
            state, regex = load_operand(state, scope)
            state, _ = state.pop(operator)
            return state, type(regex)
        return inner

    load_zero_or_more = load_postfix('*', regex.ZeroOrMore)
    load_one_or_more = load_postfix('+', regex.OneOrMore)
    load_zero_or_one = load_postfix('?', regex.ZeroOrOne)
    load_until_empty = load_postfix('!', regex.UntilEmpty)

    def load_prefix(operator: str, type: Type[regex.UnaryRegex]) -> parser.Rule[regex.Regex]:
        def inner(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
            state, _ = state.pop(operator)
            state, regex = load_operand(state, scope)
            return state, type(regex)
        return inner

    load_not = load_prefix('^', regex.Not)
    load_skip = load_prefix('~', regex.Skip)

    def load_range(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
        state, _ = state.pop('[')
        state, start = parser.token_val(state, rule_name='literal')
        state, _ = state.pop('-')
        state, end = parser.token_val(state, rule_name='literal')
        state, _ = state.pop(']')
        return state, regex.Range(start, end)

    def load_special(state: tokens.TokenStream, scope: parser.Scope[regex.Regex]) -> parser.StateAndResult[regex.Regex]:
        state, _ = state.pop('\\')
        state, val = parser.token_val(state)
        if val == 'w':
            return state, regex.Whitespace()
        else:
            return state, regex.literal(val)

    load_operation = parser.Or[regex.Regex](
        [load_zero_or_more, load_one_or_more, load_zero_or_one, load_until_empty, load_not, load_skip])

    load_operand = parser.Or[regex.Regex](
        [load_range, load_or, load_and, load_special, load_literal])

    load_regex = parser.Or[regex.Regex]([load_operation, load_operand])

    _, rules = parser.UntilEmpty[regex.Regex](
        load_regex)(tokens_, parser.Scope[regex.Regex]())
    if len(rules) == 1:
        return rules[0]
    else:
        return regex.And(rules)
