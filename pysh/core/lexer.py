from dataclasses import dataclass
from typing import Iterable, Iterator, MutableSequence, Sequence, Sized
from . import chars, errors, regex, tokens

StateAndResult = tuple[chars.CharStream, tokens.Token]


@dataclass(frozen=True, kw_only=True, repr=False)
class RuleError(errors.UnaryError):
    rule: 'Rule'
    state: chars.CharStream

    def _repr_line(self) -> str:
        return f'lexer.RuleError(rule={self.rule},state={self.state}, msg={self.msg})'

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


@dataclass(frozen=True)
class Lexer(Sized, Iterable[Rule]):
    rules: Sequence[Rule]

    def __str__(self) -> str:
        return f"Lexer({','.join([str(rule) for rule in self.rules])})"

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self) -> Iterator[Rule]:
        return iter(self.rules)

    def __add__(self, rhs: 'Lexer') -> 'Lexer':
        return Lexer(list(self.rules)+list(rhs.rules))

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
            tokens_.append(token)
        return tokens.TokenStream(tokens_)
