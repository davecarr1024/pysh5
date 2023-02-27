from .tokens import *
from .. import regex


@dataclass(frozen=True, kw_only=True)
class LexError(Error):
    state: CharStream
    children: Sequence[Error]


@dataclass(frozen=True, kw_only=True)
class RuleError(UnaryError):
    rule: 'Rule'


StateAndResult = tuple[CharStream, Token]


@dataclass(frozen=True)
class Rule:
    name: str
    regex_: regex.Rule

    def __call__(self, state: CharStream | str) -> StateAndResult:
        if isinstance(state, str):
            return self(CharStream.load(state))
        try:
            state, result = self.regex_(state)
            return state, Token.load(self.name, result)
        except Error as error:
            raise RuleError(
                rule=self,
                child=error,
            )

    @staticmethod
    def literal(value: str) -> 'Rule':
        return Rule(value, regex.literal(value))


@dataclass(frozen=True)
class Lexer(Sized, Iterable[Rule]):
    rules: Sequence[Rule]

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self) -> Iterator[Rule]:
        return iter(self.rules)

    def _apply_any(self, state: CharStream) -> StateAndResult:
        errors: MutableSequence[Error] = []
        for rule in self.rules:
            try:
                return rule(state)
            except Error as error:
                errors.append(error)
        raise LexError(
            state=state,
            children=errors,
        )

    def __call__(self, state: CharStream | str) -> TokenStream:
        if isinstance(state, str):
            return self(CharStream.load(state))
        tokens: MutableSequence[Token] = []
        while state:
            state, token = self._apply_any(state)
            tokens.append(token)
        return TokenStream(tokens)
