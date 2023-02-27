from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, Mapping, MutableSequence, Optional, Sequence, TypeVar
from ..lexer.tokens import *
from ..errors import *

_Result = TypeVar('_Result')


@dataclass(frozen=True, kw_only=True, repr=False)
class StateError(NaryError):
    state: TokenStream

    def _repr(self) -> str:
        return f"StateError(state={self.state},msg={self.msg})"


StateAndResult = tuple[TokenStream, _Result]

Rule = Callable[[TokenStream, 'Scope[_Result]'], StateAndResult[_Result]]


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
    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        ...


@dataclass(frozen=True, kw_only=True, repr=False)
class RuleError(Generic[_Result], StateError):
    rule: Rule[_Result]

    def _repr(self) -> str:
        return f"RuleError(rule={str(self.rule)},state={self.state},msg={self.msg})"


StateAndMultipleResult = tuple[TokenStream, Sequence[_Result]]

MultipleResultRule = Callable[[TokenStream, Scope[_Result]],
                              StateAndMultipleResult[_Result]]


class AbstractMultipleResultRule(Generic[_Result], ABC):
    @abstractmethod
    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        ...


@dataclass(frozen=True, kw_only=True, repr=False)
class MultipleResultRuleError(Generic[_Result], StateError):
    rule: MultipleResultRule[_Result]

    def _repr(self) -> str:
        return f"MultipleResultRuleError(rule={str(self.rule)},state={self.state},msg={self.msg})"


StateAndOptionalResult = tuple[TokenStream, Optional[_Result]]

OptionalResultRule = Callable[[TokenStream, Scope[_Result]],
                              StateAndOptionalResult[_Result]]


class AbstractOptionalResultRule(Generic[_Result], ABC):
    @abstractmethod
    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndOptionalResult[_Result]:
        ...


@dataclass(frozen=True)
class AbstractLiteral(AbstractRule[_Result]):
    rule_name: str

    def __str__(self) -> str:
        return self.rule_name

    @abstractmethod
    def convert_result(self, token: Token) -> _Result:
        ...

    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
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

    def __str__(self) -> str:
        return self.rule_name

    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        if self.rule_name not in scope:
            raise RuleError(
                rule=self,
                state=state,
                msg=f'unknown rule {self.rule_name}'
            )
        try:
            return scope[self.rule_name](state, scope)
        except Error as error:
            raise RuleError(rule=self, state=state, children=[error])


@dataclass(frozen=True)
class And(AbstractMultipleResultRule[_Result]):
    children: Sequence[Rule[_Result]]

    def __str__(self) -> str:
        return f"({' '.join(str(child)for child in self.children)})"

    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        for child in self.children:
            try:
                state, child_result = child(state, scope)
                results.append(child_result)
            except Error as error:
                raise MultipleResultRuleError[_Result](
                    state=state, rule=self, children=[error])
        return state, results


@dataclass(frozen=True)
class Or(AbstractRule[_Result]):
    children: Sequence[Rule[_Result]]

    def __str__(self) -> str:
        return f"({' | '.join(str(child)for child in self.children)})"

    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        child_errors: MutableSequence[Error] = []
        for child in self.children:
            try:
                return child(state, scope)
            except Error as error:
                child_errors.append(error)
        raise RuleError(state=state, rule=self, children=child_errors)


@dataclass(frozen=True)
class ZeroOrMore(AbstractMultipleResultRule[_Result]):
    child: Rule[_Result]

    def __str__(self) -> str:
        return f'{self.child}*'

    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        while True:
            try:
                state, result = self.child(state, scope)
                results.append(result)
            except Error:
                return state, results


@dataclass(frozen=True)
class OneOrMore(AbstractMultipleResultRule[_Result]):
    child: Rule[_Result]

    def __str__(self) -> str:
        return f'{self.child}+'

    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        try:
            state, result = self.child(state, scope)
            results: MutableSequence[_Result] = [result]
        except Error as error:
            raise MultipleResultRuleError(
                rule=self,
                state=state,
                children=[error],
            )
        while True:
            try:
                state, result = self.child(state, scope)
                results.append(result)
            except Error:
                return state, results


@dataclass(frozen=True)
class ZeroOrOne(AbstractOptionalResultRule[_Result]):
    child: Rule[_Result]

    def __str__(self) -> str:
        return f'{self.child}?'

    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndOptionalResult[_Result]:
        try:
            return self.child(state, scope)
        except Error:
            return state, None


@dataclass(frozen=True)
class UntilEmpty(AbstractMultipleResultRule[_Result]):
    child: Rule[_Result]

    def __str__(self) -> str:
        return f'{self.child}!'

    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        while state:
            try:
                state, result = self.child(state, scope)
                results.append(result)
            except Error as error:
                raise MultipleResultRuleError(
                    rule=self,
                    state=state,
                    children=[error],
                )
        return state, results


_PartResult = TypeVar('_PartResult')


@dataclass(frozen=True)
class _AbstractFormat(Generic[_Result], Sized, Iterable[OptionalResultRule[_Result]]):
    class Part(AbstractOptionalResultRule[_PartResult]):
        ...

    @dataclass(frozen=True)
    class Pop(Part[_PartResult]):
        rule_name: str

        def __call__(self, state: TokenStream, scope: Scope[_PartResult]) -> StateAndOptionalResult[_PartResult]:
            return state.pop(self.rule_name), None

    @dataclass(frozen=True)
    class Apply(Part[_PartResult]):
        child: Rule[_PartResult]

        def __call__(self, state: TokenStream, scope: Scope[_PartResult]) -> StateAndOptionalResult[_PartResult]:
            return self.child(state, scope)

    parts: Sequence[Part[_Result]]

    def __len__(self) -> int:
        return len(self.parts)

    def __iter__(self) -> Iterator[OptionalResultRule[_Result]]:
        return iter(self.parts)

    def _apply_parts(self, state: TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        for part in self.parts:
            state, result = part(state, scope)
            if result:
                results.append(result)
        return state, results


@dataclass(frozen=True)
class Format(_AbstractFormat[_Result], AbstractRule[_Result]):
    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        state, results = self._apply_parts(state, scope)
        if len(results) != 1:
            raise RuleError(
                rule=self,
                state=state,
                msg=f'expected 1 format result got {len(results)}'
            )
        return state, results[0]


def _format_parts(*parts: str | Rule[_Result]) -> Sequence[_AbstractFormat.Part[_Result]]:
    parts_: MutableSequence[_AbstractFormat.Part[_Result]] = []
    for part in parts:
        if isinstance(part, str):
            parts_.append(_AbstractFormat.Pop(part))
        else:
            parts_.append(_AbstractFormat.Apply(part))
    return parts_


def format(*parts: str | Rule[_Result]) -> Format[_Result]:
    return Format[_Result](_format_parts(*parts))


@dataclass(frozen=True)
class MultipleResultFormat(_AbstractFormat[_Result], AbstractMultipleResultRule[_Result]):
    def __call__(self, state: TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        return self._apply_parts(state, scope)


def multiple_result_format(*parts: str | Rule[_Result]) -> MultipleResultFormat[_Result]:
    return MultipleResultFormat[_Result](_format_parts(*parts))


@dataclass(frozen=True)
class Parser(AbstractRule[_Result]):
    root_rule_name: str
    scope: Scope[_Result]

    def __call__(
            self,
            state: TokenStream,
            scope: Optional[Scope[_Result]] = None,
            rule_name: Optional[str] = None,
    ) -> StateAndResult[_Result]:
        scope = scope or self.scope
        rule_name = rule_name or self.root_rule_name
        if rule_name not in scope:
            raise RuleError(
                rule=self,
                state=state,
                msg=f'unknown rule {rule_name}',
            )
        try:
            return scope[rule_name](state, scope)
        except Error as error:
            raise RuleError(
                rule=self,
                state=state,
                children=[error],
            )
