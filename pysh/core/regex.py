from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import string
from typing import Callable, Iterable, Iterator, MutableSequence, Sequence, Sized, Type
from . import chars, errors, tokens


@dataclass(frozen=True, kw_only=True, repr=False)
class RegexError(errors.NaryError):
    state: chars.CharStream
    regex: 'Regex'

    def _repr_line(self) -> str:
        return f'RegexError(regex={self.regex}, state={self.state}, msg={self.msg})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True)
class Result(Sized, Iterable[chars.Char]):
    chars_: Sequence[chars.Char] = field(default_factory=list[chars.Char])

    def __len__(self) -> int:
        return len(self.chars_)

    def __iter__(self) -> Iterator[chars.Char]:
        return iter(self.chars_)

    def __add__(self, rhs: 'Result') -> 'Result':
        return Result(list(self.chars_)+list(rhs.chars_))

    def position(self) -> chars.Position:
        if not self:
            return chars.Position()
        return list(self.chars_)[0].position

    def val(self) -> str:
        return ''.join([char.val for char in self.chars_])

    def token(self, rule_name: str) -> tokens.Token:
        return tokens.Token(rule_name, self.val(), self.position())


StateAndResult = tuple[chars.CharStream, Result]
Regex = Callable[[chars.CharStream], StateAndResult]


class _AbstractRegex(ABC):
    @abstractmethod
    def __call__(self, state: chars.CharStream) -> StateAndResult:
        ...


@dataclass(frozen=True)
class Any(_AbstractRegex):
    def __str__(self) -> str:
        return '.'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        return state.tail(), Result([state.head()])


@dataclass(frozen=True)
class Literal(_AbstractRegex):
    val: str

    def __post_init__(self):
        if len(self.val) != 1:
            raise errors.Error(msg=f'invalid literal val {self.val}')

    def __str__(self) -> str:
        return self.val

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        if state.head().val != self.val:
            raise RegexError(regex=self, state=state,
                             msg=f'expected regex literal {self.val} got {state.head()}')
        return state.tail(), Result([state.head()])


def literal(val: str) -> Regex:
    if len(val) == 1:
        return Literal(val)
    return And([literal(c) for c in val])


@dataclass(frozen=True)
class Range(_AbstractRegex):
    start: str
    end: str

    def __post_init__(self):
        if len(self.start) != 1 or len(self.end) != 1:
            raise errors.Error(msg=f'invalid range {self}')

    def __str__(self) -> str:
        return f'[{self.start}-{self.end}]'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        if state.head().val < self.start or state.head().val > self.end:
            raise RegexError(regex=self, state=state)
        return state.tail(), Result([state.head()])


@dataclass(frozen=True)
class _NaryRegex(_AbstractRegex):
    children: Sequence[Regex]


@dataclass(frozen=True)
class And(_NaryRegex):
    def __str__(self) -> str:
        return f"({''.join([str(child) for child in self.children])})"

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        result = Result()
        for child in self.children:
            try:
                state, child_result = child(state)
                result += child_result
            except errors.Error as error:
                raise RegexError(regex=self, state=state, children=[error])
        return state, result


@dataclass(frozen=True)
class Or(_NaryRegex):
    def __str__(self) -> str:
        return f"({'|'.join([str(child) for child in self.children])})"

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        child_errors: MutableSequence[errors.Error] = []
        for child in self.children:
            try:
                return child(state)
            except errors.Error as error:
                child_errors.append(error)
        raise RegexError(regex=self, state=state, children=child_errors)


@dataclass(frozen=True)
class UnaryRegex(_AbstractRegex):
    child: Regex


@dataclass(frozen=True)
class ZeroOrMore(UnaryRegex):
    def __str__(self) -> str:
        return f'{self.child}*'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        result = Result()
        while True:
            try:
                state, child_result = self.child(state)
                result += child_result
            except errors.Error:
                return state, result


@dataclass(frozen=True)
class OneOrMore(UnaryRegex):
    def __str__(self) -> str:
        return f'{self.child}+'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        try:
            state, result = self.child(state)
        except errors.Error as error:
            raise RegexError(regex=self, state=state, children=[error])
        while True:
            try:
                state, child_result = self.child(state)
                result += child_result
            except errors.Error:
                return state, result


@dataclass(frozen=True)
class ZeroOrOne(UnaryRegex):
    def __str__(self) -> str:
        return f'{self.child}?'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        try:
            return self.child(state)
        except errors.Error:
            return state, Result()


@dataclass(frozen=True)
class UntilEmpty(UnaryRegex):
    def __str__(self) -> str:
        return f'{self.child}?'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        result = Result()
        while state:
            try:
                state, child_result = self.child(state)
                result += child_result
            except errors.Error as error:
                raise RegexError(regex=self, state=state, children=[error])
        return state, result


@dataclass(frozen=True)
class Not(UnaryRegex):
    def __str__(self) -> str:
        return f'^{self.child}'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        try:
            self.child(state)
        except errors.Error:
            return state.tail(), Result()
        raise RegexError(regex=self, state=state)


@dataclass(frozen=True)
class Skip(UnaryRegex):
    def __str__(self) -> str:
        return f'~{self.child}'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        try:
            state, _ = self.child(state)
            return state, Result()
        except errors.Error as error:
            raise RegexError(regex=self, state=state, children=[error])


@dataclass(frozen=True)
class Whitespace(_AbstractRegex):
    def __str__(self) -> str:
        return '\\w'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        return Or([literal(c) for c in string.whitespace])(state)


def load(input: str) -> Regex:
    from . import lexer, parser

    operators = '()|[-]^*+?!\\~'
    lexer_ = lexer.Lexer([
        lexer.Rule(operator, literal(operator))
        for operator in operators
    ]+[
        lexer.Rule('literal', Any())
    ])
    tokens_ = lexer_(input)

    def load_and(state: tokens.TokenStream, scope: parser.Scope[Regex]) -> parser.StateAndResult[Regex]:
        state, _ = state.pop('(')
        state, rules = parser.OneOrMore[Regex](load_regex)(state, scope)
        state, _ = state.pop(')')
        if len(rules) == 1:
            return state, rules[0]
        return state, And(rules)

    def load_or(state: tokens.TokenStream, scope: parser.Scope[Regex]) -> parser.StateAndResult[Regex]:
        def load_tail(state: tokens.TokenStream, scope: parser.Scope[Regex]) -> parser.StateAndResult[Regex]:
            state, _ = state.pop('|')
            return load_regex(state, scope)

        state, _ = state.pop('(')
        state, head = load_regex(state, scope)
        state, tails = parser.OneOrMore[Regex](load_tail)(state, scope)
        state, _ = state.pop(')')
        return state, Or([head] + list(tails))

    load_literal = parser.Literal[Regex](
        'literal', lambda token: literal(token.val))

    def load_postfix(operator: str, type: Type[UnaryRegex]) -> parser.Rule[Regex]:
        def inner(state: tokens.TokenStream, scope: parser.Scope[Regex]) -> parser.StateAndResult[Regex]:
            state, regex = load_operand(state, scope)
            state, _ = state.pop(operator)
            return state, type(regex)
        return inner

    load_zero_or_more = load_postfix('*', ZeroOrMore)
    load_one_or_more = load_postfix('+', OneOrMore)
    load_zero_or_one = load_postfix('?', ZeroOrOne)
    load_until_empty = load_postfix('!', UntilEmpty)

    def load_prefix(operator: str, type: Type[UnaryRegex]) -> parser.Rule[Regex]:
        def inner(state: tokens.TokenStream, scope: parser.Scope[Regex]) -> parser.StateAndResult[Regex]:
            state, _ = state.pop(operator)
            state, regex = load_operand(state, scope)
            return state, type(regex)
        return inner

    load_not = load_prefix('^', Not)
    load_skip = load_prefix('~', Skip)

    def load_range(state: tokens.TokenStream, scope: parser.Scope[Regex]) -> parser.StateAndResult[Regex]:
        state, _ = state.pop('[')
        state, start = parser.token_val(state, rule_name='literal')
        state, _ = state.pop('-')
        state, end = parser.token_val(state, rule_name='literal')
        state, _ = state.pop(']')
        return state, Range(start, end)

    def load_special(state: tokens.TokenStream, scope: parser.Scope[Regex]) -> parser.StateAndResult[Regex]:
        state, _ = state.pop('\\')
        state, val = parser.token_val(state)
        if val == 'w':
            return state, Whitespace()
        else:
            return state, literal(val)

    load_operation = parser.Or[Regex](
        [load_zero_or_more, load_one_or_more, load_zero_or_one, load_until_empty, load_not, load_skip])

    load_operand = parser.Or[Regex](
        [load_range, load_or, load_and, load_special, load_literal])

    load_regex = parser.Or[Regex]([load_operation, load_operand])

    _, rules = parser.UntilEmpty[Regex](
        load_regex)(tokens_, parser.Scope[Regex]())
    if len(rules) == 1:
        return rules[0]
    else:
        return And(rules)
