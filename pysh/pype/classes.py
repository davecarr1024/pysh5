from abc import ABC, abstractmethod
from typing import Any, Type
from .vals import *


class AbstractClass(ABC, Val):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    def object_type(self) -> Type['Object']:
        return Object

    def instantiate(self, *args: Any, **kwargs: Any) -> 'Object':
        object_ = self.object_type(
            self, self.members.as_child(), *args, **kwargs)
        object_.members.bind(object_)
        return object_

    def __call__(self, scope: Scope, args: Args) -> Val:
        object_ = self.instantiate()
        if '__init__' in object_:
            object_['__init__'](scope, args)
        return object_


@dataclass(frozen=True)
class Class(AbstractClass):
    _name: str
    _members: Scope

    @property
    def name(self) -> str:
        return self._name

    @property
    def members(self) -> Scope:
        return self._members


@dataclass(frozen=True)
class Object(Val):
    class_: AbstractClass
    _members: Scope

    @property
    def members(self) -> Scope:
        return self._members

    def __call__(self, scope: Scope, args: Args) -> Val:
        if '__call__' not in self:
            raise Error(msg=f'calling uncallable object {self}')
        return self['__call__'](scope, args)
