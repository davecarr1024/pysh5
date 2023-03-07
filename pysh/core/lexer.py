from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Iterable, Iterator, MutableSequence, Sequence, Sized
from . import chars, errors, regex, tokens

StateAndResult = tuple[chars.CharStream, tokens.Token]


@dataclass(frozen=True, kw_only=True, repr=False)
class RuleError(errors.UnaryError):
    rule: 'Rule'
    state: chars.CharStream

    def _repr_line(self) -> str:
        return f'RuleError(rule={self.rule},state={self.state}, msg={self.msg})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True, kw_only=True, repr=False)
class LexError(errors.NaryError):
    lexer: 'Lexer'
    state: chars.CharStream

    def _repr_line(self) -> str:
        return f'LexError(lexer={self.lexer},state={self.state}, msg={self.msg})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True)
class Rule:
    name: str
    regex_: regex.Regex

    def __str__(self) -> str:
        return f'{self.name}={self.regex_}'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        try:
            state, result = self.regex_(state)
            return state, result.token(self.name)
        except errors.Error as error:
            raise RuleError(rule=self, state=state, child=error)

    @staticmethod
    def load(rule_name: str, regex_: str | regex.Regex | None = None) -> 'Rule':
        if regex_ is None:
            regex_ = regex.literal(rule_name)
        if isinstance(regex_, str):
            regex_ = regex.load(regex_)
        return Rule(rule_name, regex_)

    @staticmethod
    def whitespace() -> 'Rule':
        return Rule.load('ws', '~(\\w+)')


@dataclass(frozen=True)
class Lexer(Sized, Iterable[Rule]):
    rules: Sequence[Rule] = field(default_factory=list[Rule])

    def __str__(self) -> str:
        return f"Lexer({','.join([str(rule) for rule in self.rules])})"

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self) -> Iterator[Rule]:
        return iter(self.rules)

    def _rules_dict(self) -> OrderedDict[str, regex.Regex]:
        rules = OrderedDict[str, regex.Regex]()
        for rule in self.rules:
            rules[rule.name] = rule.regex_
        return rules

    def __or__(self, rhs: 'Lexer | Rule') -> 'Lexer':
        if isinstance(rhs, Rule):
            rhs = Lexer([rhs])
        lhs_rules = self._rules_dict()
        rhs_rules = rhs._rules_dict()
        for rule_name in set(lhs_rules.keys()) & set(rhs_rules.keys()):
            lhs_rule = lhs_rules[rule_name]
            rhs_rule = rhs_rules[rule_name]
            if lhs_rule != rhs_rule:
                raise errors.Error(
                    msg=f'redefining lex rule {rule_name}: {lhs_rule} != {rhs_rule}')
        return Lexer.load(**(lhs_rules | rhs_rules))

    def _apply_any(self, state: chars.CharStream) -> StateAndResult:
        errors_: MutableSequence[errors.Error] = []
        for rule in self.rules:
            try:
                return rule(state)
            except errors.Error as error:
                errors_.append(error)
        raise LexError(lexer=self, state=state, children=errors_)

    def __call__(self, state: chars.CharStream | str) -> tokens.TokenStream:
        if isinstance(state, str):
            return self(chars.CharStream.load(state))
        tokens_: MutableSequence[tokens.Token] = []
        while state:
            state, token = self._apply_any(state)
            if token.val:
                tokens_.append(token)
        return tokens.TokenStream(tokens_)

    @staticmethod
    def load(**regexes: str | regex.Regex) -> 'Lexer':
        return Lexer([Rule.load(rule_name, regex) for rule_name, regex in regexes.items()])

    @staticmethod
    def literal(*vals: str) -> 'Lexer':
        return Lexer([Rule.load(val) for val in vals])
