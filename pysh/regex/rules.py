from abc import ABC, abstractmethod
from dataclasses import dataclass
from .errors import *
from .state import *


@dataclass(frozen=True)
class RuleError(Error):
    children: list[Error]
    state: 'State'
    rule: 'Rule'


class Rule(ABC):
    @abstractmethod
    def __call__(self, state: State) -> StateAndResult:
        ...


@dataclass(frozen=True)
class Literal(Rule):
    val: Char

    def __call__(self, state: State) -> StateAndResult:
        if state.head() != self.val:
            raise RuleError(msg=None, state=state, rule=self, children=[])
        return state.tail(), Result(state.head().val)


@dataclass(frozen=True)
class And(Rule):
    children: list[Rule]

    def __call__(self, state: State) -> StateAndResult:
        result = Result('')
        for child in self.children:
            try:
                state, child_result = child(state)
                result += child_result
            except Error as error:
                raise RuleError(state=state, rule=self,
                                msg=None, children=[error])
        return state, result


@dataclass(frozen=True)
class Or(Rule):
    children: list[Rule]

    def __call__(self, state: State) -> StateAndResult:
        child_errors: list[Error] = []
        for child in self.children:
            try:
                return child(state)
            except Error as error:
                child_errors.append(error)
        raise RuleError(state=state, rule=self,
                        msg=None, children=child_errors)


@dataclass(frozen=True)
class ZeroOrMore(Rule):
    child: Rule

    def __call__(self, state: State) -> StateAndResult:
        result = Result()
        while True:
            try:
                state, child_result = self.child(state)
                result += child_result
            except Error:
                return state, result


@dataclass(frozen=True)
class OneOrMore(Rule):
    child: Rule

    def __call__(self, state: State) -> StateAndResult:
        try:
            state, result = self.child(state)
        except Error as error:
            raise RuleError(msg=None, state=state, rule=self, children=[error])
        while True:
            try:
                state, child_result = self.child(state)
                result += child_result
            except Error:
                return state, result


@dataclass(frozen=True)
class ZeroOrOne(Rule):
    child: Rule

    def __call__(self, state: State) -> StateAndResult:
        try:
            return self.child(state)
        except Error:
            return state, Result()


@dataclass(frozen=True)
class UntilEmpty(Rule):
    child: Rule

    def __call__(self, state: State) -> StateAndResult:
        result = Result()
        while state:
            try:
                state, child_result = self.child(state)
                result += child_result
            except Error as error:
                raise RuleError(msg=None, rule=self,
                                state=state, children=[error])
        return state, result
