from abc import ABC, abstractmethod
from dataclasses import dataclass
from . import statements, vals
from ..core import errors


class AbstractFunc(ABC, vals.Val):
    @property
    @abstractmethod
    def params(self) -> vals.Params:
        ...


class BindableFunc(AbstractFunc):
    def __post_init__(self):
        if not self.params:
            raise errors.Error(msg=f'bindable func must have non-empty params')

    @property
    def can_bind(self) -> bool:
        return True

    def bind(self, object_: vals.Val) -> vals.Val:
        return BoundFunc(self, object_)


@dataclass(frozen=True)
class BoundFunc(AbstractFunc):
    func: AbstractFunc
    object_: vals.Val

    @property
    def params(self) -> vals.Params:
        return self.func.params.tail

    def __call__(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
        return self.func(scope, args.prepend(vals.Arg(self.object_)))
