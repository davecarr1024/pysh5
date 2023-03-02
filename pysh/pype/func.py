from dataclasses import dataclass
from . import builtins_, funcs, statements, vals


@dataclass(frozen=True)
class Func(funcs.AbstractFunc):
    _params: vals.Params
    body: statements.Block

    @property
    def params(self) -> vals.Params:
        return self._params

    def __call__(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
        result = self.body.eval(self._params.bind(scope, args))
        if result.has_return_value():
            return result.return_value()
        else:
            return builtins_.none


@dataclass(frozen=True)
class Method(Func, funcs.BindableFunc):
    ...
