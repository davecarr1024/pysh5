from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import string
from typing import Callable, Iterable, Iterator, MutableSequence, Sequence, Sized, Type
from . import chars, errors, tokens


@dataclass(frozen=True, kw_only=True, repr=False)
class RegexError(errors.NaryError):
    state: chars.CharStream
    regex: 'Regex'

    def _repr_line(self) -> str:
        return f'RegexError(regex={self.regex}, state={self.state}, msg={self.msg})'

    def __repr__(self) -> str:
        return self._repr(0)


@dataclass(frozen=True)
class Result(Sized, Iterable[chars.Char]):
    chars_: Sequence[chars.Char] = field(default_factory=list[chars.Char])

    def __len__(self) -> int:
        return len(self.chars_)

    def __iter__(self) -> Iterator[chars.Char]:
        return iter(self.chars_)

    def __add__(self, rhs: 'Result') -> 'Result':
        return Result(list(self.chars_)+list(rhs.chars_))

    def position(self) -> chars.Position:
        if not self:
            return chars.Position()
        return list(self.chars_)[0].position

    def val(self) -> str:
        return ''.join([char.val for char in self.chars_])

    def token(self, rule_name: str) -> tokens.Token:
        return tokens.Token(rule_name, self.val(), self.position())


StateAndResult = tuple[chars.CharStream, Result]
Regex = Callable[[chars.CharStream], StateAndResult]


class _AbstractRegex(ABC):
    @abstractmethod
    def __call__(self, state: chars.CharStream) -> StateAndResult:
        ...


@dataclass(frozen=True)
class Any(_AbstractRegex):
    def __str__(self) -> str:
        return '.'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        return state.tail(), Result([state.head()])


@dataclass(frozen=True)
class Literal(_AbstractRegex):
    val: str

    def __post_init__(self):
        if len(self.val) != 1:
            raise errors.Error(msg=f'invalid literal val {self.val}')

    def __str__(self) -> str:
        return self.val

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        if state.head().val != self.val:
            raise RegexError(regex=self, state=state,
                             msg=f'expected regex literal {self.val} got {state.head()}')
        return state.tail(), Result([state.head()])


def literal(val: str) -> Regex:
    if len(val) == 1:
        return Literal(val)
    return And([literal(c) for c in val])


@dataclass(frozen=True)
class Range(_AbstractRegex):
    start: str
    end: str

    def __post_init__(self):
        if len(self.start) != 1 or len(self.end) != 1:
            raise errors.Error(msg=f'invalid range {self}')

    def __str__(self) -> str:
        return f'[{self.start}-{self.end}]'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        if state.head().val < self.start or state.head().val > self.end:
            raise RegexError(regex=self, state=state)
        return state.tail(), Result([state.head()])


@dataclass(frozen=True)
class _NaryRegex(_AbstractRegex):
    children: Sequence[Regex]


@dataclass(frozen=True)
class And(_NaryRegex):
    def __str__(self) -> str:
        return f"({''.join([str(child) for child in self.children])})"

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        result = Result()
        for child in self.children:
            try:
                state, child_result = child(state)
                result += child_result
            except errors.Error as error:
                raise RegexError(regex=self, state=state, children=[error])
        return state, result


@dataclass(frozen=True)
class Or(_NaryRegex):
    def __str__(self) -> str:
        return f"({'|'.join([str(child) for child in self.children])})"

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        child_errors: MutableSequence[errors.Error] = []
        for child in self.children:
            try:
                return child(state)
            except errors.Error as error:
                child_errors.append(error)
        raise RegexError(regex=self, state=state, children=child_errors)


@dataclass(frozen=True)
class _UnaryRegex(_AbstractRegex):
    child: Regex


@dataclass(frozen=True)
class ZeroOrMore(_UnaryRegex):
    def __str__(self) -> str:
        return f'{self.child}*'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        result = Result()
        while True:
            try:
                state, child_result = self.child(state)
                result += child_result
            except errors.Error:
                return state, result


@dataclass(frozen=True)
class OneOrMore(_UnaryRegex):
    def __str__(self) -> str:
        return f'{self.child}+'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        try:
            state, result = self.child(state)
        except errors.Error as error:
            raise RegexError(regex=self, state=state, children=[error])
        while True:
            try:
                state, child_result = self.child(state)
                result += child_result
            except errors.Error:
                return state, result


@dataclass(frozen=True)
class ZeroOrOne(_UnaryRegex):
    def __str__(self) -> str:
        return f'{self.child}?'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        try:
            return self.child(state)
        except errors.Error:
            return state, Result()


@dataclass(frozen=True)
class UntilEmpty(_UnaryRegex):
    def __str__(self) -> str:
        return f'{self.child}?'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        result = Result()
        while state:
            try:
                state, child_result = self.child(state)
                result += child_result
            except errors.Error as error:
                raise RegexError(regex=self, state=state, children=[error])
        return state, result


@dataclass(frozen=True)
class Not(_UnaryRegex):
    def __str__(self) -> str:
        return f'^{self.child}'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        try:
            self.child(state)
        except errors.Error:
            return state.tail(), Result([state.head()])
        raise RegexError(regex=self, state=state)


@dataclass(frozen=True)
class Skip(_UnaryRegex):
    def __str__(self) -> str:
        return f'~{self.child}'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        try:
            state, _ = self.child(state)
            return state, Result()
        except errors.Error as error:
            raise RegexError(regex=self, state=state, children=[error])


@dataclass(frozen=True)
class Whitespace(_AbstractRegex):
    def __str__(self) -> str:
        return '\\w'

    def __call__(self, state: chars.CharStream) -> StateAndResult:
        return Or([literal(c) for c in string.whitespace])(state)


def load(input: str) -> Regex:
    from . import lexer as lexer_lib, parser

    def and_args(args: Sequence[Regex]) -> Regex:
        if len(args) == 0:
            raise errors.Error(msg='loading empty sub-regex')
        if len(args) == 1:
            return args[0]
        else:
            return And(args)

    literal_lex_rule = lexer_lib.Rule.load(
        'literal',
        Not(
            Or([
                literal(operator)
                for operator in '()[-]|*+?!^~.\\'
            ])
        )
    )

    class RangeLoader(parser.SingleResultRule[Regex]):
        def __call__(self, state: tokens.TokenStream, scope: parser.Scope[Regex]) -> parser.StateAndResult[Regex]:
            state, _ = state.pop('[')
            state, start_token = state.pop('literal')
            state, _ = state.pop('-')
            state, end_token = state.pop('literal')
            state, _ = state.pop(']')
            return state, Range(start_token.val, end_token.val)

        @property
        def lexer(self) -> lexer_lib.Lexer:
            return lexer_lib.Lexer.literal('[', '-', ']') | literal_lex_rule

    class SpecialLoader(parser.SingleResultRule[Regex]):
        def __call__(self, state: tokens.TokenStream, scope: parser.Scope[Regex]) -> parser.StateAndResult[Regex]:
            state, _ = state.pop('\\')
            state, token = state.pop()
            if token.val == 'w':
                return state, Whitespace()
            elif token.val == 'd':
                return state, Range('0', '9')
            return state, literal(token.val)

        @property
        def lexer(self) -> lexer_lib.Lexer:
            return lexer_lib.Lexer.literal('\\')

    def suffix_loader(operator: str, type: Type[_UnaryRegex]) -> parser.SingleResultRule[Regex]:
        return parser.combine(
            parser.Ref[Regex]('operand'),
            operator,
        )

    def prefix_loader(operator: str, type: Type[_UnaryRegex]) -> parser.SingleResultRule[Regex]:
        return parser.Combiner[Regex].load(
            operator,
            parser.Combiner[Regex].Func(
                parser.MultipleResultCombiner[Regex].load(
                    parser.Ref[Regex]('operand'),
                ),
                lambda results: type(results[0]),
            ),
        )

    _, result = parser.Parser[Regex](
        'root',
        parser.Scope[Regex]({
            'root': parser.Combiner[Regex].load(
                parser.Combiner[Regex].Func(
                    parser.UntilEmpty[Regex](
                        parser.Ref[Regex]('regex'),
                    ),
                    and_args
                ),
            ),
            'regex': parser.Or[Regex]([
                parser.Ref[Regex]('operation'),
                parser.Ref[Regex]('operand'),
            ]),
            'operation': parser.Or[Regex]([
                suffix_loader('*', ZeroOrMore),
                suffix_loader('+', OneOrMore),
                suffix_loader('?', ZeroOrOne),
                suffix_loader('!', UntilEmpty),
                prefix_loader('^', Not),
                prefix_loader('~', Skip),
            ]),
            'operand': parser.Or[Regex]([
                parser.Ref[Regex]('any'),
                parser.Ref[Regex]('special'),
                parser.Ref[Regex]('or'),
                parser.Ref[Regex]('and'),
                parser.Ref[Regex]('range'),
                parser.Ref[Regex]('literal'),
            ]),
            'special': SpecialLoader(),
            'any': parser.Literal(lexer_lib.Rule.load('.'), lambda _: Any()),
            'range': RangeLoader(),
            'and': parser.Combiner[Regex].load(
                '(',
                parser.Combiner[Regex].Func(
                    parser.OneOrMore[Regex](
                        parser.Ref[Regex]('regex'),
                    ),
                    and_args
                ),
                ')',
            ),
            'or': parser.Combiner[Regex].load(
                '(',
                parser.Combiner[Regex].load(
                    parser.Combiner[Regex].Func(
                        parser.MultipleResultCombiner.load(
                            parser.Ref[Regex]('regex'),
                            parser.OneOrMore[Regex](
                                parser.Combiner.load(
                                    '|',
                                    parser.Ref[Regex]('regex'),
                                ),
                            )
                        ),
                        Or
                    )
                ),
                ')',
            ),
            'literal': parser.Literal(
                literal_lex_rule,
                lambda token: literal(token.val)
            ),
        })
    )(input)
    return result
