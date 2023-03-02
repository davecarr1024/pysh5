from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Type
from . import vals
from ..core import errors


class AbstractClass(ABC, vals.Val):
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

    def __call__(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
        object_ = self.instantiate()
        if '__init__' in object_:
            object_['__init__'](scope, args)
        return object_


@dataclass(frozen=True)
class Class(AbstractClass):
    _name: str
    _members: vals.Scope

    @property
    def name(self) -> str:
        return self._name

    @property
    def members(self) -> vals.Scope:
        return self._members


@dataclass(frozen=True)
class Object(vals.Val):
    class_: AbstractClass
    _members: vals.Scope

    @property
    def members(self) -> vals.Scope:
        return self._members

    def __call__(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
        if '__call__' not in self:
            raise errors.Error(msg=f'calling uncallable object {self}')
        return self['__call__'](scope, args)
