from dataclasses import dataclass
from ..core import parser
from . import builtins_, exprs, funcs, params, statements, vals


@dataclass(frozen=True)
class Func(funcs.AbstractFunc):
    _name: str
    _params: params.Params
    body: statements.Block

    @property
    def name(self) -> str:
        return self._name

    @property
    def params(self) -> params.Params:
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


@dataclass(frozen=True)
class Decl(statements.AbstractDecl):
    func: Func

    @property
    def val(self) -> exprs.Expr:
        return exprs.ref(self.func)

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[statements.Statement]:
        raise NotImplementedError()
