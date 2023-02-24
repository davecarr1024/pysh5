from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, Mapping, MutableSequence, Optional, Sequence, TypeVar
from ..lexer.tokens import *
from ..errors import *

_Result = TypeVar('_Result')


@dataclass(frozen=True, kw_only=True)
class StateError(Error):
    state: TokenStream
    children: Sequence[Error] = field(default_factory=list[Error])


StateAndResult = tuple[TokenStream, _Result]

Rule = Callable[['Scope[_Result]', TokenStream], StateAndResult[_Result]]


@dataclass(frozen=True)
class Scope(Generic[_Result], Mapping[str, Rule[_Result]]):
    _vals: Mapping[str, Rule[_Result]] = field(
        default_factory=dict[str, Rule[_Result]])

    def __getitem__(self, name: str) -> Rule[_Result]:
        return self._vals[name]

    def __len__(self) -> int:
        return len(self._vals)

    def __iter__(self) -> Iterator[str]:
        return iter(self._vals)


class AbstractRule(Generic[_Result], ABC):
    @abstractmethod
    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndResult[_Result]:
        ...


@dataclass(frozen=True, kw_only=True)
class RuleError(Generic[_Result], StateError):
    rule: Rule[_Result]


StateAndMultipleResult = tuple[TokenStream, Sequence[_Result]]

MultipleResultRule = Callable[[Scope[_Result], TokenStream],
                              StateAndMultipleResult[_Result]]


class AbstractMultipleResultRule(Generic[_Result], ABC):
    @abstractmethod
    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndMultipleResult[_Result]:
        ...


@dataclass(frozen=True, kw_only=True)
class MultipleResultRuleError(Generic[_Result], StateError):
    rule: MultipleResultRule[_Result]


StateAndOptionalResult = tuple[TokenStream, Optional[_Result]]

OptionalResultRule = Callable[[Scope[_Result], TokenStream],
                              StateAndOptionalResult[_Result]]


class AbstractOptionalResultRule(Generic[_Result], ABC):
    @abstractmethod
    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndOptionalResult[_Result]:
        ...


@dataclass(frozen=True)
class AbstractLiteral(AbstractRule[_Result]):
    rule_name: str

    @abstractmethod
    def convert_result(self, token: Token) -> _Result:
        ...

    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndResult[_Result]:
        if state.head().rule_name == self.rule_name:
            return state.tail(), self.convert_result(state.head())
        else:
            raise RuleError(
                rule=self,
                state=state,
                children=[],
                msg=f'rule_name {state.head().rule_name} != {self.rule_name}')


@dataclass(frozen=True)
class Literal(AbstractLiteral[_Result]):
    rule_converter: Callable[[Token], _Result]

    def convert_result(self, token: Token) -> _Result:
        return self.rule_converter(token)


@dataclass(frozen=True)
class Ref(AbstractRule[_Result]):
    rule_name: str

    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndResult[_Result]:
        if self.rule_name not in scope:
            raise RuleError(
                rule=self,
                state=state,
                msg=f'unknown rule {self.rule_name}'
            )
        try:
            return scope[self.rule_name](scope, state)
        except Error as error:
            raise RuleError(rule=self, state=state, children=[error])


@dataclass(frozen=True)
class And(AbstractMultipleResultRule[_Result]):
    children: Sequence[Rule[_Result]]

    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        for child in self.children:
            try:
                state, child_result = child(scope, state)
                results.append(child_result)
            except Error as error:
                raise MultipleResultRuleError[_Result](
                    state=state, rule=self, children=[error])
        return state, results


@dataclass(frozen=True)
class Or(AbstractRule[_Result]):
    children: Sequence[Rule[_Result]]

    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndResult[_Result]:
        child_errors: MutableSequence[Error] = []
        for child in self.children:
            try:
                return child(scope, state)
            except Error as error:
                child_errors.append(error)
        raise RuleError(state=state, rule=self, children=child_errors)


@dataclass(frozen=True)
class ZeroOrMore(AbstractMultipleResultRule[_Result]):
    child: Rule[_Result]

    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        while True:
            try:
                state, result = self.child(scope, state)
                results.append(result)
            except Error:
                return state, results


@dataclass(frozen=True)
class OneOrMore(AbstractMultipleResultRule[_Result]):
    child: Rule[_Result]

    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndMultipleResult[_Result]:
        try:
            state, result = self.child(scope, state)
            results: MutableSequence[_Result] = [result]
        except Error as error:
            raise MultipleResultRuleError(
                rule=self,
                state=state,
                children=[error],
            )
        while True:
            try:
                state, result = self.child(scope, state)
                results.append(result)
            except Error:
                return state, results


@dataclass(frozen=True)
class ZeroOrOne(AbstractOptionalResultRule[_Result]):
    child: Rule[_Result]

    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndOptionalResult[_Result]:
        try:
            return self.child(scope, state)
        except Error:
            return state, None


@dataclass(frozen=True)
class UntilEmpty(AbstractMultipleResultRule[_Result]):
    child: Rule[_Result]

    def __call__(self, scope: Scope[_Result], state: TokenStream) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        while state:
            try:
                state, result = self.child(scope, state)
                results.append(result)
            except Error as error:
                raise MultipleResultRuleError(
                    rule=self,
                    state=state,
                    children=[error],
                )
        return state, results
