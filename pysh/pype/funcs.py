from abc import ABC, abstractmethod
from .statements import *


class AbstractFunc(ABC, Val):
    @property
    @abstractmethod
    def params(self) -> Params:
        ...


class BindableFunc(AbstractFunc):
    def __post_init__(self):
        if not self.params:
            raise Error(msg=f'bindable func must have non-empty params')

    @property
    def can_bind(self) -> bool:
        return True

    def bind(self, object_: Val) -> Val:
        return BoundFunc(self, object_)


@dataclass(frozen=True)
class BoundFunc(AbstractFunc):
    func: AbstractFunc
    object_: Val

    @property
    def params(self) -> Params:
        return self.func.params.tail

    def __call__(self, scope: Scope, args: Args) -> Val:
        return self.func(scope, args.prepend(Arg(self.object_)))
