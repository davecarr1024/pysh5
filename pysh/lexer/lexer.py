from typing import OrderedDict
from .tokens import *
from .. import regex


@dataclass(frozen=True)
class LexError(Error):
    state: CharStream
    children: Sequence[Error]


@dataclass(frozen=True)
class Lexer:
    rules: OrderedDict[str, regex.Rule]

    def _apply_any(self, state: CharStream) -> tuple[CharStream, Token]:
        rule_errors: MutableSequence[Error] = []
        for rule_name, rule in self.rules.items():
            try:
                state, result = rule(state)
                return state, Token.load(rule_name, result)
            except Error as error:
                rule_errors.append(error)
        raise LexError(state, rule_errors, msg='failed to apply any rules')

    def __call__(self, state: CharStream | str) -> TokenStream:
        if isinstance(state, str):
            return self(CharStream.load(state))
        tokens: MutableSequence[Token] = []
        while state:
            state, token = self._apply_any(state)
            tokens.append(token)
        return TokenStream(tokens)
