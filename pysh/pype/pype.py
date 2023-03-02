from . import builtins_, statements, vals


def load(input: str) -> statements.Statement:
    raise NotImplementedError(input)


def eval(input: str, scope: vals.Scope | None = None) -> vals.Val:
    result = load(input).eval(scope or vals.Scope())
    if result.has_return_value():
        return result.return_value()
    return builtins_.none
