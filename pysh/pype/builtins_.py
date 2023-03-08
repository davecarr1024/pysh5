from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import operator
from typing import Any, Callable, Generic, Mapping, Type, TypeVar
from ..core import errors, lexer,  parser, regex, tokens
from . import classes, funcs, vals


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
    def object_type(self) -> Type['classes.Object']:
        return self._object_type


@dataclass(frozen=True)
class Object(classes.Object, ABC):
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

    @staticmethod
    def parser_() -> parser.Parser[vals.Val]:
        return parser.Parser[vals.Val](
            'object',
            parser.Scope[vals.Val]({
                'object': parser.Or[vals.Val]([
                    parser.Ref[vals.Val]('int'),
                    parser.Ref[vals.Val]('none'),
                ]),
                'int': _IntObject.loader(),
                'none': _NoneObject.loader(),
            })
        )

    @classmethod
    @abstractmethod
    def loader(cls) -> parser.SingleResultRule[vals.Val]:
        ...


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
    def params(self) -> vals.Params:
        return vals.Params([vals.Param('lhs'), vals.Param('rhs')])

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
    def loader(cls) -> parser.SingleResultRule[vals.Val]:
        def convert_token(token: tokens.Token) -> vals.Val:
            try:
                return int_(int(token.val))
            except ValueError as error:
                raise errors.Error(
                    msg=f'failed to read int literal {token}: {error}')

        return parser.Literal[vals.Val](
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


def int_(val: int) -> classes.Object:
    return _IntClass.instantiate(val)


class _NoneObject(Object):
    @classmethod
    def from_val(cls, scope: vals.Scope, val: vals.Val) -> Any:
        return None

    @classmethod
    def loader(cls) -> parser.SingleResultRule[vals.Val]:
        return parser.Literal[vals.Val](
            lexer.Rule.load('none'),
            lambda _: none
        )


_NoneClass = _Class(
    'None',
    vals.Scope({}),
    _NoneObject,
)

none = _NoneClass.instantiate()
