from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, MutableSequence, Sequence, Sized
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
            raise errors.Error(msg='position from empty regex result')
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
