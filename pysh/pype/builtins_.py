import operator
from typing import Callable, Generic, TypeVar
from .classes import *
from .funcs import *


@dataclass(frozen=True)
class _BuiltinClass(AbstractClass):
    _name: str
    _members: Scope
    _object_type: Type['_BuiltinObject']

    @property
    def name(self) -> str:
        return self._name

    @property
    def members(self) -> Scope:
        return self._members

    @property
    def object_type(self) -> Type['Object']:
        return self._object_type


@dataclass(frozen=True)
class _BuiltinObject(Object):
    class_: AbstractClass = field(compare=False, repr=False)
    _members: Scope = field(compare=False, repr=False)

    @staticmethod
    def to_val(val: Any) -> Val:
        ctors: Mapping[Type[Any], Callable[[Any], Val]] = {
            int: int_,
        }
        if type(val) not in ctors:
            raise Error(msg=f'unexpected builtin type {type(val)}')
        return ctors[type(val)](val)

    @classmethod
    @abstractmethod
    def from_val(cls, scope: Scope, val: Val) -> Any:
        ...


_BuiltinValue = TypeVar('_BuiltinValue')


@dataclass(frozen=True)
class _BuiltinValueObject(_BuiltinObject, Generic[_BuiltinValue]):
    value: _BuiltinValue


_BuiltinExtractor = Callable[[Scope, Val], Any]


@dataclass(frozen=True)
class _BuiltinBinaryFunc(BindableFunc):
    lhs: _BuiltinExtractor
    rhs: _BuiltinExtractor
    operator: Callable[[Any, Any], Any]

    @property
    def params(self) -> Params:
        return Params([Param('lhs'), Param('rhs')])

    def __call__(self, scope: Scope, args: Args) -> Val:
        if len(args) != 2:
            raise Error(
                msg=f'builtin binary func expects 2 args got {len(args)}')
        lhs = self.lhs(scope, args.args[0].val)
        rhs = self.lhs(scope, args.args[1].val)
        return _BuiltinValueObject.to_val(self.operator(lhs, rhs))


def _binary_func(
        object_type: Type[_BuiltinObject],
        operator: Callable[[Any, Any], Any]) -> _BuiltinBinaryFunc:
    return _BuiltinBinaryFunc(
        object_type.from_val,
        object_type.from_val,
        operator,
    )


class _IntObject(_BuiltinValueObject[int]):
    @classmethod
    def from_val(cls, scope: Scope, val: Val) -> Any:
        if isinstance(val, _IntObject):
            return val.value
        raise Error(msg=f'can''t convert {val} to int')


_IntClass = _BuiltinClass(
    'int',
    Scope({
        '__add__': _binary_func(_IntObject, operator.add),
    }),
    _IntObject,
)


def int_(val: int) -> Object:
    return _IntClass.instantiate(val)


class _NoneObject(_BuiltinObject):
    @classmethod
    def from_val(cls, scope: Scope, val: Val) -> Any:
        return None


_NoneClass = _BuiltinClass(
    'None',
    Scope({}),
    _NoneObject,
)

none = _NoneClass.instantiate()
