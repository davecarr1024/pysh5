from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from typing import Callable, Generic, Iterable, Iterator, Mapping, MutableSequence, Optional, Sequence, Sized, Type,  TypeVar, Union, overload
from . import errors, lexer, tokens

_Result = TypeVar('_Result')
_ConvertResult = TypeVar('_ConvertResult')

StateAndSingleResult = tuple[tokens.TokenStream, _Result]
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
class ParseError(StateError):
    rule_name: str

    def _repr_line(self) -> str:
        return f'ParseError(rule_name={self.rule_name},state={self.state},msg={repr(self.msg)})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True)
class Scope(Generic[_Result]):
    rules: Mapping[str, 'SingleResultRule[_Result]'] = field(
        default_factory=dict[str, 'SingleResultRule[_Result]'])

    def __post_init__(self):
        for _, rule in self.rules.items():
            assert rule is not None

    def __str__(self) -> str:
        return f"{{{', '.join([f'{name}={rule}' for name, rule in self.rules.items()])}}}"

    def __len__(self) -> int:
        return len(self.rules)

    def __getitem__(self, name: str) -> 'SingleResultRule[_Result]':
        if name not in self.rules:
            raise KeyError(f'unknown rule {name}')
        return self.rules[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self.rules)

    def __or__(self, rhs: 'Scope[_Result]') -> 'Scope[_Result]':
        return Scope[_Result](dict(self.rules) | dict(rhs.rules))


class Rule(Generic[_Result], ABC):
    @property
    @abstractmethod
    def lexer_(self) -> lexer.Lexer:
        ...

    @abstractmethod
    def single(self) -> 'SingleResultRule[_Result]':
        ...

    @abstractmethod
    def optional(self) -> 'OptionalResultRule[_Result]':
        ...

    @abstractmethod
    def multiple(self) -> 'MultipleResultRule[_Result]':
        ...


_ChildRuleType = TypeVar('_ChildRuleType', bound=Rule)


@dataclass(frozen=True)
class _UnaryRule(Generic[_Result, _ChildRuleType], Rule[_Result]):
    child: _ChildRuleType

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}({','.join([f'{f.name}={getattr(self,f.name)}' for f in fields(self)])})"

    @property
    def lexer_(self) -> lexer.Lexer:
        return self.child.lexer_


_AdapterResult = TypeVar('_AdapterResult')
_AdapterConvertResult = TypeVar('_AdapterConvertResult')

_AndArgs = Union[
    'NoResultRule[_Result]',
    'OptionalResultRule[_Result]',
    'SingleResultRule[_Result]',
    'MultipleResultRule[_Result]',
    lexer.Rule,
    str,
    'Type[_AbstractParsable[_Result]]',
]

_RandArgs = Union[
    str,
    lexer.Rule,
    'Type[_AbstractParsable[_Result]]',
]


class NoResultRule(Rule[_Result]):
    @abstractmethod
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> tokens.TokenStream:
        ...

    @overload
    def __and__(self, rhs: 'NoResultRule[_Result]') -> 'NoResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'OptionalResultRule[_Result]') -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'SingleResultRule[_Result]') -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'MultipleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: lexer.Rule) -> 'NoResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: str) -> 'NoResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'Type[Parsable[_ParsableType]]') -> 'SingleResultAnd[_Result]':
        ...

    def __and__(self, rhs: _AndArgs) -> 'Rule[_Result]':
        if isinstance(rhs, NoResultRule):
            return NoResultAnd([self, rhs])
        elif isinstance(rhs, OptionalResultRule):
            return OptionalResultAnd([self, rhs])
        elif isinstance(rhs, SingleResultRule):
            return SingleResultAnd([self, rhs])
        elif isinstance(rhs, MultipleResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, lexer.Rule):
            return NoResultAnd([self, LexRule(rhs)])
        elif isinstance(rhs, str):
            return NoResultAnd([self, LexRule.load(rhs)])
        elif issubclass(rhs, _AbstractParsable):
            return SingleResultAnd([self, rhs.ref()])
        else:
            raise TypeError(type(rhs))

    @overload
    def __rand__(self, lhs: str) -> 'NoResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: lexer.Rule) -> 'NoResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: Type['Parsable[_ParsableType]']) -> 'SingleResultAnd[_Result]':
        ...

    def __rand__(self, lhs: _RandArgs) -> 'Rule[_Result]':
        if isinstance(lhs, str) or isinstance(lhs, lexer.Rule):
            return NoResultAnd([LexRule.load(lhs), self])
        elif issubclass(lhs, Parsable):
            return SingleResultAnd([lhs.ref(), self])
        else:
            raise TypeError(type(lhs))

    def single(self) -> 'SingleResultRule[_Result]':
        raise errors.Error(
            msg=f'unable to convert NoResultRule {self} to SingleResultRule')

    def optional(self) -> 'OptionalResultRule[_Result]':
        @dataclass(frozen=True)
        class Adapter(_UnaryRule[_AdapterResult, 'NoResultRule[_AdapterResult]'], OptionalResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndOptionalResult[_AdapterResult]:
                return self.child(state, scope), None

        return Adapter[_Result](self)

    def multiple(self) -> 'MultipleResultRule[_Result]':
        class Adapter(_UnaryRule[_AdapterResult, NoResultRule[_AdapterResult]], MultipleResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndMultipleResult[_AdapterResult]:
                return self.child(state, scope), []
        return Adapter[_Result](self)

    def with_lexer(self, lexer_: lexer.Lexer) -> 'NoResultRule[_Result]':
        class Adapter(_UnaryRule[_AdapterResult, NoResultRule[_AdapterResult]], NoResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> tokens.TokenStream:
                return self.child(state, scope)

            @property
            def lexer_(self) -> lexer.Lexer:
                return super().lexer_ | lexer_

        return Adapter(self)

    def with_scope(self, scope: Scope[_Result]) -> 'NoResultRule[_Result]':
        @dataclass(frozen=True)
        class Adapter(_UnaryRule[_AdapterResult, NoResultRule[_AdapterResult]], NoResultRule[_AdapterResult]):
            scope: Scope[_AdapterResult]

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> tokens.TokenStream:
                return self.child(state, scope | self.scope)

            @property
            def lexer_(self) -> lexer.Lexer:
                lexer_ = super().lexer_
                for rule in self.scope.rules.values():
                    lexer_ |= rule.lexer_
                return lexer_

        return Adapter[_Result](self, scope)


class SingleResultRule(Rule[_Result]):
    @abstractmethod
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndSingleResult[_Result]:
        ...

    @overload
    def __and__(self, rhs: 'NoResultRule[_Result]') -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'OptionalResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'SingleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'MultipleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: lexer.Rule) -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: str) -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'Type[Parsable[_ParsableType]]') -> 'MultipleResultAnd[_Result]':
        ...

    def __and__(self, rhs: _AndArgs) -> 'Rule[_Result]':
        if isinstance(rhs, NoResultRule):
            return SingleResultAnd([self, rhs])
        elif isinstance(rhs, OptionalResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, SingleResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, MultipleResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, lexer.Rule):
            return SingleResultAnd([self, LexRule(rhs)])
        elif isinstance(rhs, str):
            return SingleResultAnd([self, LexRule.load(rhs)])
        elif issubclass(rhs, _AbstractParsable):
            return MultipleResultAnd([self, rhs.ref()])
        else:
            raise TypeError(type(rhs))

    @overload
    def __rand__(self, lhs: str) -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: lexer.Rule) -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: Type['Parsable[_ParsableType]']) -> 'MultipleResultAnd[_Result]':
        ...

    def __rand__(self, lhs: _RandArgs) -> 'Rule[_Result]':
        if isinstance(lhs, str) or isinstance(lhs, lexer.Rule):
            return SingleResultAnd([LexRule.load(lhs), self])
        elif issubclass(lhs, Parsable):
            return MultipleResultAnd([lhs.ref(), self])
        else:
            raise TypeError(type(lhs))

    def __or__(self, rhs: 'SingleResultRule[_Result]') -> 'Or[_Result]':
        return Or[_Result]([self, rhs])

    def single(self) -> 'SingleResultRule[_Result]':
        return self

    def optional(self) -> 'OptionalResultRule[_Result]':
        @dataclass(frozen=True)
        class Adapter(_UnaryRule[_AdapterResult, SingleResultRule[_AdapterResult]], OptionalResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndOptionalResult[_AdapterResult]:
                return self.child(state, scope)
        return Adapter[_Result](self)

    def multiple(self) -> 'MultipleResultRule[_Result]':
        class Adapter(_UnaryRule[_AdapterResult, SingleResultRule[_AdapterResult]], MultipleResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndMultipleResult[_AdapterResult]:
                state, result = self.child(state, scope)
                return state, [result]
        return Adapter[_Result](self)

    def convert(self, func: Callable[[_Result], _Result]) -> 'SingleResultRule[_Result]':
        @dataclass(frozen=True)
        class Adapter(_UnaryRule[_AdapterResult, SingleResultRule[_AdapterResult]], SingleResultRule[_AdapterResult]):
            func: Callable[[_AdapterResult], _AdapterResult]

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndSingleResult[_AdapterResult]:
                state, result = self.child(state, scope)
                return state, self.func(result)

        return Adapter[_Result](self, func)

    def convert_type(self, func: Callable[[_Result], _ConvertResult]) -> 'SingleResultRule[_ConvertResult]':
        @dataclass(frozen=True)
        class Adapter(
            Generic[_AdapterResult, _AdapterConvertResult],
            _UnaryRule[_AdapterConvertResult,
                       SingleResultRule[_AdapterResult]],
            SingleResultRule[_AdapterConvertResult],
        ):
            func: Callable[[_AdapterResult], _AdapterConvertResult]

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterConvertResult]) -> StateAndSingleResult[_AdapterConvertResult]:
                state, result = self.child(state, Scope[_AdapterResult]())
                return state, self.func(result)

        return Adapter[_Result, _ConvertResult](self, func)

    def with_lexer(self, lexer_: lexer.Lexer) -> 'SingleResultRule[_Result]':
        class Adapter(_UnaryRule[_AdapterResult, SingleResultRule[_AdapterResult]], SingleResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndSingleResult[_AdapterResult]:
                return self.child(state, scope)

            @property
            def lexer_(self) -> lexer.Lexer:
                return super().lexer_ | lexer_

        return Adapter(self)

    def with_scope(self, scope: Scope[_Result]) -> 'SingleResultRule[_Result]':
        @dataclass(frozen=True)
        class Adapter(_UnaryRule[_AdapterResult, SingleResultRule[_AdapterResult]], SingleResultRule[_AdapterResult]):
            scope: Scope[_AdapterResult]

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndSingleResult[_AdapterResult]:
                return self.child(state, scope | self.scope)

            @property
            def lexer_(self) -> lexer.Lexer:
                lexer_ = super().lexer_
                for rule in self.scope.rules.values():
                    lexer_ |= rule.lexer_
                return lexer_

        return Adapter[_Result](self, scope)

    def zero_or_more(self) -> 'ZeroOrMore[_Result]':
        return ZeroOrMore[_Result](self)

    def one_or_more(self) -> 'OneOrMore[_Result]':
        return OneOrMore[_Result](self)

    def zero_or_one(self) -> 'ZeroOrOne[_Result]':
        return ZeroOrOne[_Result](self)

    def until_empty(self) -> 'UntilEmpty[_Result]':
        return UntilEmpty[_Result](self)

    def until_token(self, lex_rule: lexer.Rule | str) -> 'UntilToken[_Result]':
        if isinstance(lex_rule, str):
            lex_rule = lexer.Rule.load(lex_rule)
        return UntilToken[_Result](self, lex_rule)

    def eval(self, input: str | tokens.TokenStream, scope: Optional[Scope[_Result]] = None) -> StateAndSingleResult[_Result]:
        if isinstance(input, str):
            input = self.lexer_(input)
        if scope is None:
            scope = Scope[_Result]()
        return self(input, scope)


class OptionalResultRule(Rule[_Result]):
    @abstractmethod
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndOptionalResult[_Result]:
        ...

    @overload
    def __and__(self, rhs: 'NoResultRule[_Result]') -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'OptionalResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'SingleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'MultipleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: lexer.Rule) -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: str) -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'Type[Parsable[_ParsableType]]') -> 'MultipleResultAnd[_Result]':
        ...

    def __and__(self, rhs: _AndArgs) -> 'Rule[_Result]':
        if isinstance(rhs, NoResultRule):
            return OptionalResultAnd([self, rhs])
        elif isinstance(rhs, OptionalResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, SingleResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, MultipleResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, lexer.Rule):
            return OptionalResultAnd([self, LexRule(rhs)])
        elif isinstance(rhs, str):
            return OptionalResultAnd([self, LexRule.load(rhs)])
        elif issubclass(rhs, _AbstractParsable):
            return MultipleResultAnd([self, rhs.ref()])
        else:
            raise TypeError(type(rhs))

    @overload
    def __rand__(self, lhs: str) -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: lexer.Rule) -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: Type['Parsable[_ParsableType]']) -> 'MultipleResultAnd[_Result]':
        ...

    def __rand__(self, lhs: _RandArgs) -> 'Rule[_Result]':
        if isinstance(lhs, str) or isinstance(lhs, lexer.Rule):
            return OptionalResultAnd([LexRule.load(lhs), self])
        elif issubclass(lhs, Parsable):
            return MultipleResultAnd([lhs.ref(), self])
        else:
            raise TypeError(type(lhs))

    def single(self) -> SingleResultRule[_Result]:
        class Adapter(_UnaryRule[_AdapterResult, OptionalResultRule[_AdapterResult]], SingleResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndSingleResult[_AdapterResult]:
                state, result = self.child(state, scope)
                if result is None:
                    raise RuleError(rule=self, state=state,
                                    msg=f'failed to get result from {self.child}')
                else:
                    return state, result
        return Adapter[_Result](self)

    def single_or(self, default: _Result) -> SingleResultRule[_Result]:
        @dataclass(frozen=True)
        class Adapter(_UnaryRule[_AdapterResult, OptionalResultRule[_AdapterResult]], SingleResultRule[_AdapterResult]):
            default: _AdapterResult

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndSingleResult[_AdapterResult]:
                state, result = self.child(state, scope)
                if result is None:
                    return state, self.default
                else:
                    return state, result

        return Adapter[_Result](self, default)

    def optional(self) -> 'OptionalResultRule[_Result]':
        return self

    def multiple(self) -> 'MultipleResultRule[_Result]':
        class Adapter(_UnaryRule[_AdapterResult, OptionalResultRule[_AdapterResult]], MultipleResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndMultipleResult[_AdapterResult]:
                state, result = self.child(state, scope)
                if result is None:
                    return state, []
                else:
                    return state, [result]
        return Adapter[_Result](self)

    def convert(self, func: Callable[[Optional[_Result]], _Result]) -> 'SingleResultRule[_Result]':
        @dataclass(frozen=True)
        class Adapter(_UnaryRule[_AdapterResult, OptionalResultRule[_AdapterResult]], SingleResultRule[_AdapterResult]):
            func: Callable[[Optional[_AdapterResult]], _AdapterResult]

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndSingleResult[_AdapterResult]:
                state, result = self.child(state, scope)
                return state, self.func(result)

        return Adapter[_Result](self, func)

    def convert_type(self, func: Callable[[Optional[_Result]], _ConvertResult]) -> 'SingleResultRule[_ConvertResult]':
        @dataclass(frozen=True)
        class Adapter(
            Generic[_AdapterResult, _AdapterConvertResult],
            _UnaryRule[_AdapterConvertResult,
                       OptionalResultRule[_AdapterResult]],
            SingleResultRule[_AdapterConvertResult],
        ):
            func: Callable[[Optional[_AdapterResult]], _AdapterConvertResult]

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterConvertResult]) -> StateAndSingleResult[_AdapterConvertResult]:
                state, result = self.child(state, Scope[_AdapterResult]())
                return state, self.func(result)

        return Adapter[_Result, _ConvertResult](self, func)

    def with_lexer(self, lexer_: lexer.Lexer) -> 'OptionalResultRule[_Result]':
        class Adapter(_UnaryRule[_AdapterResult, OptionalResultRule[_AdapterResult]], OptionalResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndOptionalResult[_AdapterResult]:
                return self.child(state, scope)

            @property
            def lexer_(self) -> lexer.Lexer:
                return super().lexer_ | lexer_

        return Adapter(self)

    def with_scope(self, scope: Scope[_Result]) -> 'OptionalResultRule[_Result]':
        @dataclass(frozen=True)
        class Adapter(_UnaryRule[_AdapterResult, OptionalResultRule[_AdapterResult]], OptionalResultRule[_AdapterResult]):
            scope: Scope[_AdapterResult]

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndOptionalResult[_AdapterResult]:
                return self.child(state, scope | self.scope)

            @property
            def lexer_(self) -> lexer.Lexer:
                lexer_ = super().lexer_
                for rule in self.scope.rules.values():
                    lexer_ |= rule.lexer_
                return lexer_

        return Adapter[_Result](self, scope)


class MultipleResultRule(Rule[_Result]):
    @abstractmethod
    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        ...

    @overload
    def __and__(self, rhs: 'NoResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'OptionalResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'SingleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'MultipleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: lexer.Rule) -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: str) -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'Type[Parsable[_ParsableType]]') -> 'MultipleResultAnd[_Result]':
        ...

    def __and__(self, rhs: _AndArgs) -> 'MultipleResultAnd[_Result]':
        if isinstance(rhs, NoResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, OptionalResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, SingleResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, MultipleResultRule):
            return MultipleResultAnd([self, rhs])
        elif isinstance(rhs, lexer.Rule) or isinstance(rhs, str):
            return MultipleResultAnd([self, LexRule.load(rhs)])
        elif issubclass(rhs, _AbstractParsable):
            return MultipleResultAnd([self, rhs.ref()])
        else:
            raise TypeError(type(rhs))

    @overload
    def __rand__(self, lhs: str) -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: lexer.Rule) -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: Type['Parsable[_ParsableType]']) -> 'MultipleResultAnd[_Result]':
        ...

    def __rand__(self, lhs: _RandArgs) -> 'Rule[_Result]':
        if isinstance(lhs, str) or isinstance(lhs, lexer.Rule):
            return MultipleResultAnd([LexRule.load(lhs), self])
        elif issubclass(lhs, Parsable):
            return MultipleResultAnd([lhs.ref(), self])
        else:
            raise TypeError(type(lhs))

    def single(self) -> SingleResultRule[_Result]:
        class Adapter(_UnaryRule[_AdapterResult, MultipleResultRule[_AdapterResult]], SingleResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndSingleResult[_AdapterResult]:
                state, results = self.child(state, scope)
                if len(results) != 1:
                    raise RuleError(
                        rule=self, state=state, msg=f'expected 1 result from {self.child} got {len(results)}')
                return state, results[0]
        return Adapter[_Result](self)

    def optional(self) -> OptionalResultRule[_Result]:
        class Adapter(_UnaryRule[_AdapterResult, MultipleResultRule[_AdapterResult]], OptionalResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndOptionalResult[_AdapterResult]:
                state, results = self.child(state, scope)
                if len(results) == 0:
                    return state, None
                elif len(results) == 1:
                    return state, results[0]
                else:
                    raise RuleError(
                        rule=self, state=state, msg=f'expected 0 or 1 results from {self.child} got {len(results)}')
        return Adapter[_Result](self)

    def multiple(self) -> 'MultipleResultRule[_Result]':
        return self

    def convert(self, func: Callable[[Sequence[_Result]], _Result]) -> 'SingleResultRule[_Result]':
        @dataclass(frozen=True)
        class Adapter(_UnaryRule[_AdapterResult, MultipleResultRule[_AdapterResult]], SingleResultRule[_AdapterResult]):
            func: Callable[[Sequence[_AdapterResult]], _AdapterResult]

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndSingleResult[_AdapterResult]:
                state, result = self.child(state, scope)
                return state, self.func(result)

        return Adapter[_Result](self, func)

    def convert_type(self, func: Callable[[Sequence[_Result]], _ConvertResult]) -> 'SingleResultRule[_ConvertResult]':
        @dataclass(frozen=True)
        class Adapter(
            Generic[_AdapterResult, _AdapterConvertResult],
            _UnaryRule[_AdapterConvertResult,
                       MultipleResultRule[_AdapterResult]],
            SingleResultRule[_AdapterConvertResult],
        ):
            func: Callable[[Sequence[_AdapterResult]], _AdapterConvertResult]

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterConvertResult]) -> StateAndSingleResult[_AdapterConvertResult]:
                state, results = self.child(state, Scope[_AdapterResult]())
                return state, self.func(results)
        return Adapter[_Result, _ConvertResult](self, func)

    def with_lexer(self, lexer_: lexer.Lexer) -> 'MultipleResultRule[_Result]':
        class Adapter(_UnaryRule[_AdapterResult, MultipleResultRule[_AdapterResult]], MultipleResultRule[_AdapterResult]):
            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndMultipleResult[_AdapterResult]:
                return self.child(state, scope)

            @property
            def lexer_(self) -> lexer.Lexer:
                return super().lexer_ | lexer_

        return Adapter(self)

    def with_scope(self, scope: Scope[_Result]) -> 'MultipleResultRule[_Result]':
        @dataclass(frozen=True)
        class Adapter(_UnaryRule[_AdapterResult, MultipleResultRule[_AdapterResult]], MultipleResultRule[_AdapterResult]):
            scope: Scope[_AdapterResult]

            def __call__(self, state: tokens.TokenStream, scope: Scope[_AdapterResult]) -> StateAndMultipleResult[_AdapterResult]:
                return self.child(state, scope | self.scope)

            @property
            def lexer_(self) -> lexer.Lexer:
                lexer_ = super().lexer_
                for rule in self.scope.rules.values():
                    lexer_ |= rule.lexer_
                return lexer_

        return Adapter[_Result](self, scope)


@dataclass(frozen=True)
class Ref(SingleResultRule[_Result]):
    rule_name: str

    def __str__(self) -> str:
        return self.rule_name

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndSingleResult[_Result]:
        if self.rule_name not in scope:
            raise KeyError(f'unknown rule {self.rule_name}')
        try:
            return scope[self.rule_name].single()(state, scope)
        except errors.Error as error:
            raise ParseError(rule_name=self.rule_name,
                             state=state, children=[error])

    @property
    def lexer_(self) -> lexer.Lexer:
        return lexer.Lexer()


@dataclass(frozen=True)
class AbstractLiteral(SingleResultRule[_Result]):
    lex_rule: lexer.Rule

    def __str__(self) -> str:
        return f'literal({self.lex_rule})'

    @abstractmethod
    def result(self, token: tokens.Token) -> _Result:
        ...

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndSingleResult[_Result]:
        if state.head().rule_name != self.lex_rule.name:
            raise RuleError(
                rule=self, state=state, msg=f'expected {self.lex_rule.name} got {state.head().rule_name}')
        return state.tail(), self.result(state.head())

    @property
    def lexer_(self) -> lexer.Lexer:
        return lexer.Lexer([self.lex_rule])


@dataclass(frozen=True)
class Literal(AbstractLiteral[_Result]):
    func: Callable[[tokens.Token], _Result]

    def result(self, token: tokens.Token) -> _Result:
        return self.func(token)


@dataclass(frozen=True)
class ZeroOrMore(_UnaryRule[_Result, SingleResultRule[_Result]], MultipleResultRule[_Result]):
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
    def lexer_(self) -> lexer.Lexer:
        return self.child.lexer_


@dataclass(frozen=True)
class OneOrMore(_UnaryRule[_Result, SingleResultRule[_Result]], MultipleResultRule[_Result]):
    def __str__(self) -> str:
        return f'{self.child}+'

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        try:
            state, result = self.child(state, scope)
            results: MutableSequence[_Result] = [result]
        except errors.Error as error:
            raise RuleError(
                rule=self, state=state, children=[error])
        while True:
            try:
                state, result = self.child(state, scope)
                results.append(result)
            except errors.Error:
                return state, results


@dataclass(frozen=True)
class ZeroOrOne(_UnaryRule[_Result, SingleResultRule[_Result]], OptionalResultRule[_Result]):
    def __str__(self) -> str:
        return f'{self.child}?'

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndOptionalResult[_Result]:
        try:
            return self.child(state, scope)
        except errors.Error:
            return state, None


class _AbstractUntilState(_UnaryRule[_Result, SingleResultRule[_Result]], MultipleResultRule[_Result]):
    @abstractmethod
    def _is_state_finished(self, state: tokens.TokenStream) -> bool:
        ...

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        while not self._is_state_finished(state):
            try:
                state, result = self.child(state, scope)
                results.append(result)
            except errors.Error as error:
                raise RuleError(rule=self, state=state, children=[error])
        return state, results


@dataclass(frozen=True)
class UntilToken(_AbstractUntilState[_Result]):
    lex_rule: lexer.Rule

    def __str__(self) -> str:
        return f'({self.child}!{self.lex_rule})'

    def _is_state_finished(self, state: tokens.TokenStream) -> bool:
        return state.head().rule_name == self.lex_rule.name


@dataclass(frozen=True)
class UntilEmpty(_AbstractUntilState[_Result]):
    def __str__(self) -> str:
        return f'{self.child}!'

    def _is_state_finished(self, state: tokens.TokenStream) -> bool:
        return len(state) == 0


@dataclass(frozen=True)
class Parser(Generic[_Result], SingleResultRule[_Result], Mapping[str, SingleResultRule[_Result]]):
    root_rule_name: str
    scope: Scope[_Result]

    def __str__(self) -> str:
        return f'Parser(root={self.root_rule_name},scope={self.scope})'

    def __len__(self) -> int:
        return len(self.scope)

    def __iter__(self) -> Iterator[str]:
        return iter(self.scope)

    def __getitem__(self, name: str) -> SingleResultRule[_Result]:
        return self.scope[name]

    def __call__(
            self,
            state: tokens.TokenStream | str,
            scope: Optional[Scope[_Result]] = None,
            rule_name: Optional[str] = None,
    ) -> StateAndSingleResult[_Result]:
        if isinstance(state, str):
            state = self.lexer_(state)
        scope = (scope or Scope[_Result]()) | self.scope
        rule_name = rule_name or self.root_rule_name
        try:
            return self.scope[rule_name].single()(state, scope)
        except errors.Error as error:
            raise ParseError(rule_name=rule_name,
                             state=state, children=[error])

    @property
    def lexer_(self) -> lexer.Lexer:
        lexer_ = lexer.Lexer()
        for _, rule in self.scope.rules.items():
            lexer_ |= rule.lexer_
        return lexer_


@dataclass(frozen=True)
class LexRule(NoResultRule[_Result]):
    lex_rule: lexer.Rule

    def __str__(self) -> str:
        return str(self.lex_rule)

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> tokens.TokenStream:
        try:
            state, _ = state.pop(self.lex_rule.name)
            return state
        except errors.Error as error:
            raise RuleError(rule=self, state=state, children=[error])

    @property
    def lexer_(self) -> lexer.Lexer:
        return lexer.Lexer([self.lex_rule])

    @classmethod
    def load(cls, val: str | lexer.Rule) -> 'LexRule[_Result]':
        if isinstance(val, str):
            val = lexer.Rule.load(val)
        return LexRule[_Result](val)


@dataclass(frozen=True)
class _NaryRule(Generic[_Result, _ChildRuleType], Rule[_Result], Sized, Iterable[_ChildRuleType]):
    children: Sequence[_ChildRuleType]

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> Iterator[_ChildRuleType]:
        return iter(self.children)

    @property
    def lexer_(self) -> lexer.Lexer:
        lexer_ = lexer.Lexer()
        for child in self.children:
            lexer_ |= child.lexer_
        return lexer_

    def num_children_of_type(self, type: Type[_ChildRuleType]) -> int:
        return len(list(filter(lambda child: isinstance(child, type), self)))

    def _assert_num_children_of_type(self, type: Type[_ChildRuleType], expected_num_children: int) -> None:
        num_children = self.num_children_of_type(type)
        if num_children != expected_num_children:
            raise errors.Error(
                msg=f'{self} expected {expected_num_children} of type {type} but got {num_children}')


@dataclass(frozen=True)
class _AbstractAnd(_NaryRule[_Result, _ChildRuleType]):
    def __str__(self) -> str:
        return f"({' & '.join(map(str,self))})"


@dataclass(frozen=True)
class NoResultAnd(_AbstractAnd[_Result, NoResultRule[_Result]], NoResultRule[_Result]):
    @overload
    def __and__(self, rhs: 'NoResultRule[_Result]') -> 'NoResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'OptionalResultRule[_Result]') -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'SingleResultRule[_Result]') -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'MultipleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: lexer.Rule) -> 'NoResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: str) -> 'NoResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'Type[Parsable[_ParsableType]]') -> 'SingleResultAnd[_Result]':
        ...

    def __and__(self, rhs: _AndArgs) -> 'Rule[_Result]':
        if isinstance(rhs, NoResultRule):
            return NoResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, OptionalResultRule):
            return OptionalResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, SingleResultRule):
            return SingleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, MultipleResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, lexer.Rule) or isinstance(rhs, str):
            return NoResultAnd(list(self.children)+[LexRule.load(rhs)])
        elif issubclass(rhs, _AbstractParsable):
            return SingleResultAnd(list(self.children) + [rhs.ref()])
        else:
            raise TypeError(type(rhs))

    @overload
    def __rand__(self, lhs: str) -> 'NoResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: lexer.Rule) -> 'NoResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: Type['Parsable[_ParsableType]']) -> 'SingleResultAnd[_Result]':
        ...

    def __rand__(self, lhs: _RandArgs) -> 'Rule[_Result]':
        if isinstance(lhs, str) or isinstance(lhs, lexer.Rule):
            return NoResultAnd([LexRule[_Result].load(lhs)]+list(self))
        elif issubclass(lhs, Parsable):
            return SingleResultAnd([lhs.ref()] + list(self))
        else:
            raise TypeError(type(lhs))

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> tokens.TokenStream:
        for child in self:
            try:
                state = child(state, scope)
            except errors.Error as error:
                raise RuleError(rule=self, state=state, children=[error])
        return state


@dataclass(frozen=True)
class OptionalResultAnd(_AbstractAnd[_Result, OptionalResultRule[_Result] | NoResultRule[_Result]], OptionalResultRule[_Result]):
    def __post_init__(self):
        self._assert_num_children_of_type(OptionalResultRule, 1)

    @overload
    def __and__(self, rhs: 'NoResultRule[_Result]') -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'OptionalResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'SingleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'MultipleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: lexer.Rule) -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: str) -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'Type[Parsable[_ParsableType]]') -> 'MultipleResultAnd[_Result]':
        ...

    def __and__(self, rhs: _AndArgs) -> 'Rule[_Result]':
        if isinstance(rhs, NoResultRule):
            return OptionalResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, OptionalResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, SingleResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, MultipleResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, lexer.Rule) or isinstance(rhs, str):
            return OptionalResultAnd(list(self.children)+[LexRule.load(rhs)])
        elif issubclass(rhs, _AbstractParsable):
            return MultipleResultAnd(list(self.children)+[rhs.ref()])
        else:
            raise TypeError(type(rhs))

    @overload
    def __rand__(self, lhs: str) -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: lexer.Rule) -> 'OptionalResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: Type['Parsable[_ParsableType]']) -> 'MultipleResultAnd[_Result]':
        ...

    def __rand__(self, lhs: _RandArgs) -> 'Rule[_Result]':
        if isinstance(lhs, str) or isinstance(lhs, lexer.Rule):
            return OptionalResultAnd([LexRule[_Result].load(lhs)]+list(self))
        elif issubclass(lhs, Parsable):
            return MultipleResultAnd([lhs.ref()] + list(self))
        else:
            raise TypeError(type(lhs))

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndOptionalResult[_Result]:
        result: Optional[_Result] = None
        for child in self:
            try:
                state, child_result = child.optional()(state, scope)
            except errors.Error as error:
                raise RuleError(rule=self, state=state, children=[error])
            if child_result is not None:
                if result is not None:
                    raise RuleError(
                        rule=self, state=state, msg=f'_OptionalResultAnd got multiple results {result} and {child_result}')
                result = child_result
        return state, result


@dataclass(frozen=True)
class SingleResultAnd(_AbstractAnd[_Result, SingleResultRule[_Result] | NoResultRule[_Result]], SingleResultRule[_Result]):
    def __post_init__(self):
        self._assert_num_children_of_type(SingleResultRule, 1)

    @overload
    def __and__(self, rhs: 'NoResultRule[_Result]') -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'OptionalResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'SingleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'MultipleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: lexer.Rule) -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: str) -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'Type[Parsable[_ParsableType]]') -> 'MultipleResultAnd[_Result]':
        ...

    def __and__(self, rhs: _AndArgs) -> 'Rule[_Result]':
        if isinstance(rhs, NoResultRule):
            return SingleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, OptionalResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, SingleResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, MultipleResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, lexer.Rule) or isinstance(rhs, str):
            return SingleResultAnd(list(self.children)+[LexRule.load(rhs)])
        elif issubclass(rhs, _AbstractParsable):
            return MultipleResultAnd(list(self.children)+[rhs.ref()])
        else:
            raise TypeError(type(rhs))

    @overload
    def __rand__(self, lhs: str) -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: lexer.Rule) -> 'SingleResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: Type['Parsable[_ParsableType]']) -> 'MultipleResultAnd[_Result]':
        ...

    def __rand__(self, lhs: _RandArgs) -> 'Rule[_Result]':
        if isinstance(lhs, str) or isinstance(lhs, lexer.Rule):
            return SingleResultAnd([LexRule[_Result].load(lhs)]+list(self))
        elif issubclass(lhs, Parsable):
            return MultipleResultAnd([lhs.ref()] + list(self))
        else:
            raise TypeError(type(lhs))

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndSingleResult[_Result]:
        result: Optional[_Result] = None
        for child in self:
            try:
                state, child_result = child.optional()(state, scope)
            except errors.Error as error:
                raise RuleError(rule=self, state=state, children=[error])
            if child_result is not None:
                if result is not None:
                    raise RuleError(
                        rule=self, state=state, msg=f'_SingleResultAnd got multiple results {result} and {child_result}')
                result = child_result
        if result is None:
            raise RuleError(rule=self, state=state,
                            msg='_SingleResultAnd got no result')
        else:
            return state, result


@dataclass(frozen=True)
class MultipleResultAnd(_AbstractAnd[_Result, Rule[_Result]], MultipleResultRule[_Result]):
    @overload
    def __and__(self, rhs: 'NoResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'OptionalResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'SingleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'MultipleResultRule[_Result]') -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: lexer.Rule) -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: str) -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __and__(self, rhs: 'Type[Parsable[_ParsableType]]') -> 'MultipleResultAnd[_Result]':
        ...

    def __and__(self, rhs: _AndArgs) -> 'Rule[_Result]':
        if isinstance(rhs, NoResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, OptionalResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, SingleResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, MultipleResultRule):
            return MultipleResultAnd(list(self.children)+[rhs])
        elif isinstance(rhs, lexer.Rule) or isinstance(rhs, str):
            return MultipleResultAnd(list(self.children)+[LexRule.load(rhs)])
        elif issubclass(rhs, _AbstractParsable):
            return MultipleResultAnd(list(self.children)+[rhs.ref()])
        else:
            raise TypeError(type(rhs))

    @overload
    def __rand__(self, lhs: str) -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: lexer.Rule) -> 'MultipleResultAnd[_Result]':
        ...

    @overload
    def __rand__(self, lhs: Type['Parsable[_ParsableType]']) -> 'MultipleResultAnd[_Result]':
        ...

    def __rand__(self, lhs: _RandArgs) -> 'Rule[_Result]':
        if isinstance(lhs, str) or isinstance(lhs, lexer.Rule):
            return MultipleResultAnd([LexRule[_Result].load(lhs)]+list(self))
        elif issubclass(lhs, Parsable):
            return MultipleResultAnd([lhs.ref()] + list(self))
        else:
            raise TypeError(type(lhs))

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndMultipleResult[_Result]:
        results: MutableSequence[_Result] = []
        for child in self:
            try:
                state, child_results = child.multiple()(state, scope)
                results += child_results
            except errors.Error as error:
                raise RuleError(rule=self, state=state, children=[error])
        return state, results


@dataclass(frozen=True)
class Or(_NaryRule[_Result, SingleResultRule[_Result]], SingleResultRule[_Result]):
    def __str__(self) -> str:
        return f"({' | '.join(map(str,self.children))})"

    def __or__(self, rhs: SingleResultRule[_Result]) -> 'Or[_Result]':
        return Or[_Result](list(self.children)+[rhs])

    def __call__(self, state: tokens.TokenStream, scope: Scope[_Result]) -> StateAndSingleResult[_Result]:
        child_errors: MutableSequence[errors.Error] = []
        for child in self.children:
            try:
                return child(state, scope)
            except errors.Error as error:
                child_errors.append(error)
        raise RuleError(
            rule=self, state=state, children=child_errors)

    @property
    def lexer_(self) -> lexer.Lexer:
        lexer_ = lexer.Lexer()
        for child in self.children:
            lexer_ |= child.lexer_
        return lexer_


class _AbstractParsable(ABC, Generic[_Result]):
    @classmethod
    def _name(cls) -> str:
        return cls.__name__

    @classmethod
    def ref(cls) -> Ref[_Result]:
        return Ref[_Result](cls._name())

    @classmethod
    @abstractmethod
    def _types(cls) -> Sequence[Type[_Result]]:
        ...


_ParsableType = TypeVar('_ParsableType', bound='Parsable')


class Parsable(Generic[_ParsableType], _AbstractParsable[_ParsableType]):
    @classmethod
    @abstractmethod
    def _parse_rule(cls) -> SingleResultRule[_ParsableType]:
        return Or[_ParsableType]([type.ref() for type in cls._types()])

    @classmethod
    def parser_(cls) -> Parser[_ParsableType]:
        return Parser[_ParsableType](
            cls._name(),
            Scope[_ParsableType](
                {cls._name(): cls._parse_rule()} |
                {type._name(): type._parse_rule()
                 for type in cls._types()}
            )
        )


_ParsableWithContextType = TypeVar(
    '_ParsableWithContextType', bound='ParsableWithContext')
_ParsableContext = TypeVar('_ParsableContext')


class ParsableWithContext(Generic[_ParsableWithContextType, _ParsableContext], _AbstractParsable[_ParsableWithContextType]):
    @classmethod
    @abstractmethod
    def _parse_rule(cls, context: _ParsableContext) -> SingleResultRule[_ParsableWithContextType]:
        return Or[_ParsableWithContextType]([type.ref() for type in cls._types()])

    @classmethod
    def parser_(cls, context: _ParsableContext) -> Parser[_ParsableWithContextType]:
        return Parser[_ParsableWithContextType](
            cls._name(),
            Scope[_ParsableWithContextType](
                {cls._name(): cls._parse_rule(context)} |
                {type._name(): type._parse_rule(context)
                 for type in cls._types()}
            )
        )
