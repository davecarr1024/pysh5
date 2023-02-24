from .funcs import *
from .builtins_ import *


@dataclass(frozen=True)
class Func(AbstractFunc):
    _params: Params
    body: Block

    @property
    def params(self) -> Params:
        return self._params

    def __call__(self, scope: Scope, args: Args) -> Val:
        result = self.body.eval(self._params.bind(scope, args))
        if result.has_return_value():
            return result.return_value()
        else:
            return none


@dataclass(frozen=True)
class Method(Func, BindableFunc):
    ...
