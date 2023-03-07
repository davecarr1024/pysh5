from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Generic, Iterator, Mapping, MutableSequence, Optional, Sequence,  TypeVar, Union
from . import errors, lexer, tokens

_Result = TypeVar('_Result')

StateAndResult = tuple[tokens.TokenStream, _Result]
StateAndMultipleResult = tuple[tokens.TokenStream, Sequence[_Result]]
StateAndOptionalResult = tuple[tokens.TokenStream, Optional[_Result]]


@dataclass(frozen=True, kw_only=True, repr=False)
class StateError(errors.NaryError):
    state: tokens.TokenStream

    def _repr_line(self) -> str:
        return f'StateError(state={self.state}, msg={repr(self.msg)})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True, kw_only=True, repr=False)
class RuleError(Generic[_Result], StateError):
    rule: 'Rule[_Result]'

    def _repr_line(self) -> str:
        return f'RuleError(rule={self.rule}, state={self.state}, msg={repr(self.msg)})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True, kw_only=True, repr=False)
class MultipleResultRuleError(Generic[_Result], StateError):
    rule: 'MultipleResultRule[_Result]'

    def _repr_line(self) -> str:
        return f'RuleError(rule={self.rule}, state={self.state}, msg={repr(self.msg)})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True, kw_only=True, repr=False)
class OptionalResultRuleError(Generic[_Result], StateError):
    rule: 'OptionalResultRule[_Result]'

    def _repr_line(self) -> str:
        return f'RuleError(rule={self.rule}, state={self.state}, msg={repr(self.msg)})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True, kw_only=True, repr=False)
class ParseError(errors.UnaryError):
    rule_name: str

    def _repr_line(self) -> str:
        return f'ParseError(rule_name={self.rule_name},msg={repr(self.msg)})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True)
class Scope(Generic[_Result]):
    rules: Mapping[str, 'Rule[_Result]'] = field(
        default_factory=dict[str, 'Rule[_Result]'])

    def __len__(self) -> int:
        return len(self.rules)

    def __getitem__(self, name: str) -> 'Rule[_Result]':
        if name not in self.rules:
            raise errors.Error(msg=f'unknown rule {name}')
        return self.rules[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self.rules)

    def __or__(self, rhs: 'Scope[_Result]') -> 'Scope[_Result]':
        for rule_name in set(self.rules.keys()) & set(rhs.rules.keys()):
            if self.rules[rule_name] != rhs.rules[rule_name]:
                raise errors.Error(
                    msg=f'merging scopes redefines rule {rule_name}: {self.rules[rule_name]} != {rhs.rules[rule_name]}')
        return Scope[_Result](dict(self.rules) | dict(rhs.rules))


class _BaseRule(ABC):
    @property
    @abstractmethod
    def lexer(self) -> lexer.Lexer:
        ...


class Rule(Generic[_Result], _BaseRule):
    @abstractmethod
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        ...


class MultipleResultRule(Generic[_Result], _BaseRule):
    @abstractmethod
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        ...


class OptionalResultRule(Generic[_Result], _BaseRule):
    @abstractmethod
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndOptionalResult[_Result]:
        ...


@dataclass(frozen=True)
class Ref(Rule[_Result]):
    rule_name: str

    def __str__(self) -> str:
        return self.rule_name

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        if self.rule_name not in scope:
            raise RuleError(rule=self, state=state,
                            msg=f'unknown rule {self.rule_name}')
        try:
            return scope[self.rule_name](state, scope)
        except errors.Error as error:
            raise ParseError(rule_name=self.rule_name, child=error)

    @property
    def lexer(self) -> lexer.Lexer:
        return lexer.Lexer()


@dataclass(frozen=True)
class AbstractLiteral(Rule[_Result]):
    lex_rule: lexer.Rule

    def __str__(self) -> str:
        return f'literal({self.lex_rule})'

    @abstractmethod
    def result(self, token: tokens.Token) -> _Result:
        ...

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        if state.head().rule_name != self.lex_rule.name:
            raise RuleError(
                rule=self, state=state, msg=f'expected {self.lex_rule.name} got {state.head().rule_name}')
        return state.tail(), self.result(state.head())

    @property
    def lexer(self) -> lexer.Lexer:
        return lexer.Lexer([self.lex_rule])


@dataclass(frozen=True)
class Literal(AbstractLiteral[_Result]):
    convert_result: Callable[[tokens.Token], _Result]

    def result(self, token: tokens.Token) -> _Result:
        return self.convert_result(token)


@dataclass(frozen=True)
class And(MultipleResultRule[_Result]):
    children: Sequence[Rule[_Result]]

    def __str__(self) -> str:
        return f"({' '.join(map(str,self.children))})"

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

    @property
    def lexer(self) -> lexer.Lexer:
        lexer_ = lexer.Lexer()
        for child in self.children:
            lexer_ |= child.lexer
        return lexer_


@dataclass(frozen=True)
class Or(Rule[_Result]):
    children: Sequence[Rule[_Result]]

    def __str__(self) -> str:
        return f"({' | '.join(map(str,self.children))})"

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        child_errors: MutableSequence[errors.Error] = []
        for child in self.children:
            try:
                return child(state, scope)
            except errors.Error as error:
                child_errors.append(error)
        raise RuleError(rule=self, state=state, children=child_errors)

    @property
    def lexer(self) -> lexer.Lexer:
        lexer_ = lexer.Lexer()
        for child in self.children:
            lexer_ |= child.lexer
        return lexer_


@dataclass(frozen=True)
class ZeroOrMore(MultipleResultRule[_Result]):
    child: Rule[_Result]

    def __str__(self) -> str:
        return f'{self.child}*'

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        while True:
            try:
                state, result = self.child(state, scope)
                results.append(result)
            except errors.Error:
                return state, results

    @property
    def lexer(self) -> lexer.Lexer:
        return self.child.lexer


@dataclass(frozen=True)
class OneOrMore(MultipleResultRule[_Result]):
    child: Rule[_Result]

    def __str__(self) -> str:
        return f'{self.child}+'

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

    @property
    def lexer(self) -> lexer.Lexer:
        return self.child.lexer


@dataclass(frozen=True)
class ZeroOrOne(OptionalResultRule[_Result]):
    child: Rule[_Result]

    def __str__(self) -> str:
        return f'{self.child}?'

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndOptionalResult[_Result]:
        try:
            return self.child(state, scope)
        except errors.Error:
            return state, None

    @property
    def lexer(self) -> lexer.Lexer:
        return self.child.lexer


@dataclass(frozen=True)
class UntilEmpty(MultipleResultRule[_Result]):
    child: Rule[_Result]

    def __str__(self) -> str:
        return f'{self.child}!'

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

    @property
    def lexer(self) -> lexer.Lexer:
        return self.child.lexer


@dataclass(frozen=True)
class Parser(Generic[_Result], Rule[_Result], Mapping[str, Rule[_Result]]):
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
            state: tokens.TokenStream | str,
            scope: Optional[Scope[_Result]] = None,
            rule_name: Optional[str] = None,
    ) -> StateAndResult[_Result]:
        if isinstance(state, str):
            state = self.lexer(state)
        scope = (scope or Scope[_Result]()) | self.scope
        rule_name = rule_name or self.root_rule_name
        try:
            return self.scope[rule_name](state, scope)
        except errors.Error as error:
            raise ParseError(rule_name=rule_name, child=error)

    @property
    def lexer(self) -> lexer.Lexer:
        lexer_ = lexer.Lexer()
        for _, rule in self.scope.rules.items():
            lexer_ |= rule.lexer
        return lexer_


_PartResult = TypeVar('_PartResult')
_CombinerLoadArgs = Union[
    '_Combiner.Part[_Result]',
    Rule[_Result],
    OptionalResultRule[_Result],
    MultipleResultRule[_Result],
    lexer.Rule,
    str,
]


@dataclass(frozen=True)
class _Combiner(Generic[_Result], _BaseRule):
    class Part(ABC, Generic[_PartResult]):
        @abstractmethod
        def __call__(self, state: tokens.TokenStream, scope: Scope[_PartResult]) -> StateAndMultipleResult[_PartResult]:
            ...

        @property
        @abstractmethod
        def lexer(self) -> lexer.Lexer:
            ...

    @dataclass(frozen=True)
    class RulePart(Part[_PartResult]):
        rule: Rule[_PartResult]

        def __call__(self, state: tokens.TokenStream, scope: Scope[_PartResult]) -> StateAndMultipleResult[_PartResult]:
            state, result = self.rule(state, scope)
            return state, [result]

        @property
        def lexer(self) -> lexer.Lexer:
            return self.rule.lexer

    @dataclass(frozen=True)
    class OptionalResultRulePart(Part[_PartResult]):
        rule: OptionalResultRule[_PartResult]

        def __call__(self, state: tokens.TokenStream, scope: Scope[_PartResult]) -> StateAndMultipleResult[_PartResult]:
            state, result = self.rule(state, scope)
            if result is not None:
                return state, [result]
            else:
                return state, []

        @property
        def lexer(self) -> lexer.Lexer:
            return self.rule.lexer

    @dataclass(frozen=True)
    class MultipleResultRulePart(Part[_PartResult]):
        rule: MultipleResultRule[_PartResult]

        def __call__(self, state: tokens.TokenStream, scope: Scope[_PartResult]) -> StateAndMultipleResult[_PartResult]:
            return self.rule(state, scope)

        @property
        def lexer(self) -> lexer.Lexer:
            return self.rule.lexer

    @dataclass(frozen=True)
    class LiteralPart(Part[_PartResult]):
        lex_rule: lexer.Rule

        def __call__(self, state: tokens.TokenStream, scope: Scope[_PartResult]) -> StateAndMultipleResult[_PartResult]:
            state, _ = state.pop(self.lex_rule.name)
            return state, []

        @property
        def lexer(self) -> lexer.Lexer:
            return lexer.Lexer([self.lex_rule])

    @dataclass(frozen=True)
    class Func(Part[_PartResult]):
        child: MultipleResultRule[_PartResult]
        func: Callable[[Sequence[_PartResult]], _PartResult]

        def __call__(self, state: tokens.TokenStream, scope: Scope[_PartResult]) -> StateAndMultipleResult[_PartResult]:
            state, results = self.child(state, scope)
            return state, [self.func(results)]

        @property
        def lexer(self) -> lexer.Lexer:
            return self.child.lexer

    parts: Sequence[Part[_Result]]
    _lexer: lexer.Lexer = field(default_factory=lexer.Lexer, kw_only=True)

    def _apply_parts(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        for part in self.parts:
            try:
                state, part_results = part(state, scope)
                results += part_results
            except errors.Error as error:
                raise StateError(state=state, children=[error])
        return state, results

    @property
    def lexer(self) -> lexer.Lexer:
        lexer_ = self._lexer
        for part in self.parts:
            lexer_ |= part.lexer
        return lexer_

    @staticmethod
    def _load_parts(vals: Sequence[_CombinerLoadArgs]) -> Sequence[Part[_Result]]:
        parts: MutableSequence[_Combiner.Part[_Result]] = []
        for part in vals:
            if isinstance(part, _Combiner.Part):
                parts.append(part)
            elif isinstance(part, str):
                parts.append(_Combiner.LiteralPart[_Result](
                    lexer.Rule.load(part)))
            elif isinstance(part, lexer.Rule):
                parts.append(_Combiner.LiteralPart[_Result](part))
            elif isinstance(part, Rule):
                parts.append(_Combiner.RulePart(part))
            elif isinstance(part, OptionalResultRule):
                parts.append(_Combiner.OptionalResultRulePart(part))
            elif isinstance(part, MultipleResultRule):
                parts.append(_Combiner.MultipleResultRulePart(part))
            else:
                raise TypeError(type(part))
        return parts

    @classmethod
    @abstractmethod
    def load(cls) -> '_Combiner[_Result]':
        ...


@dataclass(frozen=True)
class Combiner(_Combiner[_Result], Rule[_Result]):
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndResult[_Result]:
        state, results = self._apply_parts(state, scope)
        if len(results) != 1:
            raise RuleError(rule=self, state=state,
                            msg=f'expected 1 result got {len(results)}')
        return state, results[0]

    @classmethod
    def load(cls, *parts: _CombinerLoadArgs, _lexer: Optional[lexer.Lexer] = None) -> 'Combiner[_Result]':
        return Combiner[_Result](_Combiner._load_parts(parts), _lexer=_lexer or lexer.Lexer())


@dataclass(frozen=True)
class MultipleResultCombiner(_Combiner[_Result], MultipleResultRule[_Result]):
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        return self._apply_parts(state, scope)

    @classmethod
    def load(cls, *parts: _CombinerLoadArgs, _lexer: Optional[lexer.Lexer] = None) -> 'MultipleResultCombiner[_Result]':
        return MultipleResultCombiner[_Result](_Combiner._load_parts(parts), _lexer=_lexer or lexer.Lexer())


@dataclass(frozen=True)
class OptionalResultCombiner(_Combiner[_Result], OptionalResultRule[_Result]):
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndOptionalResult[_Result]:
        state, results = self._apply_parts(state, scope)
        if not results:
            return state, None
        elif len(results) == 1:
            return state, results[0]
        else:
            raise OptionalResultRuleError(
                rule=self, state=state, msg=f'expected 0 or 1 results got {len(results)}')

    @classmethod
    def load(cls, *parts: _CombinerLoadArgs, _lexer: Optional[lexer.Lexer] = None) -> 'OptionalResultCombiner[_Result]':
        return OptionalResultCombiner[_Result](_Combiner._load_parts(parts), _lexer=_lexer or lexer.Lexer())
