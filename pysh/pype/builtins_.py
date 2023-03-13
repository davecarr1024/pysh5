from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import operator
from typing import Any, Callable, Generic, Mapping, Sequence, Type, TypeVar
from ..core import errors, lexer,  parser, tokens
from . import classes, funcs, params, vals


@dataclass(frozen=True)
class _Class(classes.AbstractClass):
    _name: str
    _members: vals.Scope
    _object_type: Type['Object']

    @property
    def name(self) -> str:
        return self._name

    @property
    def members(self) -> vals.Scope:
        return self._members

    @property
    def object_type(self) -> Type['Object']:
        return self._object_type

    def instantiate(self, *args: Any, **kwargs: Any) -> 'Object':
        object_ = self.object_type(
            self, self.members.as_child(), *args, **kwargs)
        object_.members.bind(object_)
        return object_


@dataclass(frozen=True)
class Object(parser.Parsable['Object'], classes.Object, ABC):
    class_: classes.AbstractClass = field(compare=False, repr=False)
    _members: vals.Scope = field(compare=False, repr=False)

    @staticmethod
    def to_val(val: Any) -> vals.Val:
        ctors: Mapping[Type[Any], Callable[[Any], vals.Val]] = {
            int: int_,
        }
        if type(val) not in ctors:
            raise errors.Error(
                msg=f'unexpected builtin type {type(val)}')
        return ctors[type(val)](val)

    @classmethod
    @abstractmethod
    def from_val(cls, scope: vals.Scope, val: vals.Val) -> Any:
        ...

    @classmethod
    def types(cls) -> Sequence[Type['Object']]:
        return [
            _IntObject,
            _NoneObject,
        ]


_BuiltinValue = TypeVar('_BuiltinValue')


@dataclass(frozen=True)
class _ValueObject(Object, Generic[_BuiltinValue]):
    value: _BuiltinValue


_BuiltinExtractor = Callable[[vals.Scope, vals.Val], Any]


@dataclass(frozen=True)
class _BinaryFunc(funcs.BindableFunc):
    lhs: _BuiltinExtractor
    rhs: _BuiltinExtractor
    operator: Callable[[Any, Any], Any]

    @property
    def params(self) -> params.Params:
        return params.Params([params.Param('lhs'), params.Param('rhs')])

    def __call__(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
        if len(args) != 2:
            raise errors.Error(
                msg=f'builtin binary func expects 2 args got {len(args)}')
        lhs = self.lhs(scope, args.args[0].val)
        rhs = self.lhs(scope, args.args[1].val)
        return _ValueObject.to_val(self.operator(lhs, rhs))


def _binary_func(
        object_type: Type[Object],
        operator: Callable[[Any, Any], Any]) -> _BinaryFunc:
    return _BinaryFunc(
        object_type.from_val,
        object_type.from_val,
        operator,
    )


class _IntObject(_ValueObject[int]):
    @classmethod
    def from_val(cls, scope: vals.Scope, val: vals.Val) -> Any:
        if isinstance(val, _IntObject):
            return val.value
        raise errors.Error(msg=f'can''t convert {val} to int')

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Object]:
        def convert_token(token: tokens.Token) -> Object:
            try:
                return int_(int(token.val))
            except ValueError as error:
                raise errors.Error(
                    msg=f'failed to read int literal {token}: {error}')

        return parser.Literal[Object](
            lexer.Rule.load('int', '(\\-)?(\\d)+'),
            convert_token
        )


_IntClass = _Class(
    'int',
    vals.Scope({
        '__add__': _binary_func(_IntObject, operator.add),
    }),
    _IntObject,
)


def int_(val: int) -> Object:
    return _IntClass.instantiate(val)


class _NoneObject(Object):
    @classmethod
    def from_val(cls, scope: vals.Scope, val: vals.Val) -> Any:
        return None

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Object]:
        return parser.Literal[Object](
            lexer.Rule.load('none'),
            lambda _: none
        )


_NoneClass = _Class(
    'none',
    vals.Scope({}),
    _NoneObject,
)

none = _NoneClass.instantiate()
