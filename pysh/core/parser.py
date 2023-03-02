from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Generic, Iterator, Mapping, MutableSequence, Optional, Sequence,  TypeVar
from . import errors, tokens

_Result = TypeVar('_Result')

StateAndResult = tuple[tokens.TokenStream, _Result]
StateAndMultipleResult = tuple[tokens.TokenStream, Sequence[_Result]]
StateAndOptionalResult = tuple[tokens.TokenStream, Optional[_Result]]

Rule = Callable[[tokens.TokenStream, 'Scope[_Result]'],
                StateAndResult[_Result]]
MultipleResultRule = Callable[[tokens.TokenStream,
                               'Scope[_Result]'], StateAndMultipleResult[_Result]]
OptionalResultRule = Callable[[tokens.TokenStream,
                               'Scope[_Result]'], StateAndOptionalResult[_Result]]


@dataclass(frozen=True, kw_only=True, repr=False)
class StateError(errors.NaryError):
    state: tokens.TokenStream

    def _repr_line(self) -> str:
        return f'StateError(state={self.state}, msg={repr(self.msg)})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True, kw_only=True, repr=False)
class RuleError(Generic[_Result], StateError):
    rule: Rule[_Result]

    def _repr_line(self) -> str:
        return f'RuleError(rule={self.rule}, state={self.state}, msg={repr(self.msg)})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True, kw_only=True, repr=False)
class MultipleResultRuleError(Generic[_Result], StateError):
    rule: MultipleResultRule[_Result]

    def _repr_line(self) -> str:
        return f'RuleError(rule={self.rule}, state={self.state}, msg={repr(self.msg)})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True)
class Scope(Generic[_Result], Mapping[str, Rule[_Result]]):
    rules: Mapping[str, Rule[_Result]] = field(
        default_factory=dict[str, Rule[_Result]])

    def __len__(self) -> int:
        return len(self.rules)

    def __getitem__(self, name: str) -> Rule[_Result]:
        if name not in self.rules:
            raise errors.Error(msg=f'unknown rule {name}')
        return self.rules[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self.rules)

    def __or__(self, rhs: 'Scope[_Result]') -> 'Scope[_Result]':
        return Scope[_Result](dict(self.rules) | dict(rhs.rules))


class AbstractRule(ABC, Generic[_Result]):
    @abstractmethod
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        ...


class AbstractMultipleResultRule(ABC, Generic[_Result]):
    @abstractmethod
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        ...


class AbstractOptionalResultRule(ABC, Generic[_Result]):
    @abstractmethod
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndOptionalResult[_Result]:
        ...


@dataclass(frozen=True)
class Ref(AbstractRule[_Result]):
    rule_name: str

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        if self.rule_name not in scope:
            raise RuleError(rule=self, state=state,
                            msg=f'unknown rule {self.rule_name}')
        return scope[self.rule_name](state, scope)


@dataclass(frozen=True)
class AbstractLiteral(AbstractRule[_Result]):
    rule_name: str

    @abstractmethod
    def result(self, token: tokens.Token) -> _Result:
        ...

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        if state.head().rule_name != self.rule_name:
            raise RuleError(
                rule=self, state=state, msg=f'expected {self.rule_name} got {state.head().rule_name}')
        return state.tail(), self.result(state.head())


@dataclass(frozen=True)
class Literal(AbstractLiteral[_Result]):
    convert_result: Callable[[tokens.Token], _Result]

    def result(self, token: tokens.Token) -> _Result:
        return self.convert_result(token)


def token_val(state: tokens.TokenStream, scope: Scope[str] | None = None, rule_name: str | None = None) -> StateAndResult[str]:
    if rule_name is not None and state.head().rule_name != rule_name:
        raise StateError(
            state=state, msg=f'expected {rule_name} got {state.head().rule_name}')
    return state.tail(), state.head().val


@dataclass(frozen=True)
class And(AbstractMultipleResultRule[_Result]):
    children: Sequence[Rule[_Result]]

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        for child in self.children:
            try:
                state, result = child(state, scope)
                results.append(result)
            except errors.Error as error:
                raise MultipleResultRuleError(
                    rule=self, state=state, children=[error])
        return state, results


@dataclass(frozen=True)
class Or(AbstractRule[_Result]):
    children: Sequence[Rule[_Result]]

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        child_errors: MutableSequence[errors.Error] = []
        for child in self.children:
            try:
                return child(state, scope)
            except errors.Error as error:
                child_errors.append(error)
        raise RuleError(rule=self, state=state, children=child_errors)


@dataclass(frozen=True)
class ZeroOrMore(AbstractMultipleResultRule[_Result]):
    child: Rule[_Result]

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        while True:
            try:
                state, result = self.child(state, scope)
                results.append(result)
            except errors.Error:
                return state, results


@dataclass(frozen=True)
class OneOrMore(AbstractMultipleResultRule[_Result]):
    child: Rule[_Result]

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        try:
            state, result = self.child(state, scope)
            results: MutableSequence[_Result] = [result]
        except errors.Error as error:
            raise MultipleResultRuleError(
                rule=self, state=state, children=[error])
        while True:
            try:
                state, result = self.child(state, scope)
                results.append(result)
            except errors.Error:
                return state, results


@dataclass(frozen=True)
class ZeroOrOne(AbstractOptionalResultRule[_Result]):
    child: Rule[_Result]

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndOptionalResult[_Result]:
        try:
            return self.child(state, scope)
        except errors.Error:
            return state, None


@dataclass(frozen=True)
class UntilEmpty(AbstractMultipleResultRule[_Result]):
    child: Rule[_Result]

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        while state:
            try:
                state, result = self.child(state, scope)
                results.append(result)
            except errors.Error as error:
                raise MultipleResultRuleError(
                    rule=self, state=state, children=[error])
        return state, results


@dataclass(frozen=True)
class Parser(Generic[_Result], AbstractRule[_Result], Mapping[str, Rule[_Result]]):
    root_rule_name: str
    scope: Scope[_Result]

    def __len__(self) -> int:
        return len(self.scope)

    def __iter__(self) -> Iterator[str]:
        return iter(self.scope)

    def __getitem__(self, name: str) -> Rule[_Result]:
        return self.scope[name]

    def __call__(
            self,
            state: tokens.TokenStream,
            scope: Optional[Scope[_Result]] = None,
            rule_name: Optional[str] = None,
    ) -> StateAndResult[_Result]:
        scope = scope or self.scope
        rule_name = rule_name or self.root_rule_name
        return self.scope[rule_name](state, scope)
