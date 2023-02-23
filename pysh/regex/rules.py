from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence

from .. import errors
from .chars import *


@dataclass(frozen=True)
class RuleError(errors.Error):
    children: Sequence[errors.Error]
    state: 'CharStream'
    rule: 'Rule'


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
class Literal(Rule):
    val: Char

    def __call__(self, state: CharStream) -> StateAndResult:
        if state.head() != self.val:
            raise RuleError(msg=None, state=state, rule=self, children=[])
        return state.tail(), Result([state.head()])


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
class ZeroOrMore(Rule):
    child: Rule

    def __call__(self, state: CharStream) -> StateAndResult:
        result = Result()
        while True:
            try:
                state, child_result = self.child(state)
                result += child_result
            except errors.Error:
                return state, result


@dataclass(frozen=True)
class OneOrMore(Rule):
    child: Rule

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
class ZeroOrOne(Rule):
    child: Rule

    def __call__(self, state: CharStream) -> StateAndResult:
        try:
            return self.child(state)
        except errors.Error:
            return state, Result()


@dataclass(frozen=True)
class UntilEmpty(Rule):
    child: Rule

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
