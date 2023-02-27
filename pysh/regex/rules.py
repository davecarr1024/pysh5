from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence

from .. import errors
from .chars import *


@dataclass(frozen=True, kw_only=True)
class RuleError(Error):
    state: 'CharStream'
    rule: 'Rule'
    children: Sequence[Error] = field(default_factory=list[Error])


@dataclass(frozen=True)
class Result(Sized, Iterable[Char]):
    chars_: Sequence[Char] = field(default_factory=list[Char])

    def __add__(self, rhs: 'Result') -> 'Result':
        return Result(list(self.chars_) + list(rhs.chars_))

    def __iter__(self) -> Iterator[Char]:
        return iter(self.chars_)

    def __len__(self) -> int:
        return len(self.chars_)


StateAndResult = tuple[CharStream, Result]


class Rule(ABC):
    @abstractmethod
    def __call__(self, state: CharStream) -> StateAndResult:
        ...


@dataclass(frozen=True)
class Any(Rule):
    def __call__(self, state: CharStream) -> StateAndResult:
        return state.tail(), Result([state.head()])


@dataclass(frozen=True)
class Class(Rule):
    start: str
    end: str

    def __call__(self, state: CharStream) -> StateAndResult:
        if state.head().val >= self.start and state.head().val <= self.end:
            return state.tail(), Result([state.head()])
        raise RuleError(rule=self, state=state)


@dataclass(frozen=True)
class UnaryRule(Rule):
    child: Rule


@dataclass(frozen=True)
class Not(UnaryRule):
    def __call__(self, state: CharStream) -> StateAndResult:
        try:
            _ = self.child(state)
            raise RuleError(rule=self, state=state)
        except Error:
            return state.tail(), Result([state.head()])


@dataclass(frozen=True)
class Literal(Rule):
    val: Char

    def __call__(self, state: CharStream) -> StateAndResult:
        if state.head() != self.val:
            raise RuleError(rule=self, state=state)
        return state.tail(), Result([state.head()])


def literal(value: str) -> Rule:
    if len(value) == 1:
        return Literal(Char(value))
    return And([Literal(Char(c)) for c in value])


@dataclass(frozen=True)
class And(Rule):
    children: Sequence[Rule]

    def __call__(self, state: CharStream) -> StateAndResult:
        result = Result()
        for child in self.children:
            try:
                state, child_result = child(state)
                result += child_result
            except errors.Error as error:
                raise RuleError(state=state, rule=self,
                                msg=None, children=[error])
        return state, result


@dataclass(frozen=True)
class Or(Rule):
    children: Sequence[Rule]

    def __call__(self, state: CharStream) -> StateAndResult:
        child_errors: Sequence[errors.Error] = []
        for child in self.children:
            try:
                return child(state)
            except errors.Error as error:
                child_errors.append(error)
        raise RuleError(state=state, rule=self,
                        msg=None, children=child_errors)


@dataclass(frozen=True)
class ZeroOrMore(UnaryRule):
    def __call__(self, state: CharStream) -> StateAndResult:
        result = Result()
        while True:
            try:
                state, child_result = self.child(state)
                result += child_result
            except errors.Error:
                return state, result


@dataclass(frozen=True)
class OneOrMore(UnaryRule):
    def __call__(self, state: CharStream) -> StateAndResult:
        try:
            state, result = self.child(state)
        except errors.Error as error:
            raise RuleError(msg=None, state=state, rule=self, children=[error])
        while True:
            try:
                state, child_result = self.child(state)
                result += child_result
            except errors.Error:
                return state, result


@dataclass(frozen=True)
class ZeroOrOne(UnaryRule):
    def __call__(self, state: CharStream) -> StateAndResult:
        try:
            return self.child(state)
        except errors.Error:
            return state, Result()


@dataclass(frozen=True)
class UntilEmpty(UnaryRule):
    def __call__(self, state: CharStream) -> StateAndResult:
        result = Result()
        while state:
            try:
                state, child_result = self.child(state)
                result += child_result
            except errors.Error as error:
                raise RuleError(msg=None, rule=self,
                                state=state, children=[error])
        return state, result
