from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Iterator, MutableSequence, Optional, Sequence, Sized, Type, Union
from unittest import TestCase
from . import errors, lexer, parser, tokens

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    __import__('sys').modules['unittest.util']._MAX_LENGTH = 999999999


class Val(parser.Parsable['Val']):
    @classmethod
    def _types(cls) -> Sequence[Type['Val']]:
        return [
            Int,
            Str,
            List,
        ]


@dataclass(frozen=True)
class Int(Val):
    val: int

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Val]:
        def convert_token(token: tokens.Token) -> Int:
            try:
                return Int(int(token.val))
            except ValueError as error:
                raise errors.Error(
                    msg=f'failed to convert int token {token}: {error}')

        return parser.Literal[Val](
            lexer.Rule.load('int', '\\d+'),
            convert_token,

        )


@dataclass(frozen=True)
class Str(Val):
    val: str

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Val]:
        return parser.Literal[Val](
            lexer.Rule.load('str', '"(^")*"'),
            lambda token: Str(token.val[1:-1]),
        )


@dataclass(frozen=True)
class List(Val):
    vals: Sequence[Val]

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Val]:
        return (
            '[' &
            (
                Val.ref() &
                (
                    ',' &
                    Val.ref()
                ).zero_or_more()
            ).convert(List).zero_or_one().single_or(List([])) &
            ']'
        )


class Expr(parser.Parsable['Expr']):
    @classmethod
    def _types(cls) -> Sequence[Type['Expr']]:
        return [
            Literal,
        ]


@dataclass(frozen=True)
class Literal(Expr):
    val: Val

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Expr]:
        return Val.parser_().convert_type(Literal)


@dataclass(frozen=True)
class Arg:
    val: Expr

    @staticmethod
    def parse_rule() -> parser.SingleResultRule['Arg']:
        return Expr.ref().convert_type(Arg)


@dataclass(frozen=True)
class Args(Sized, Iterable[Arg]):
    args: Sequence[Arg] = field(default_factory=list[Arg])

    def __len__(self) -> int:
        return len(self.args)

    def __iter__(self) -> Iterator[Arg]:
        return iter(self.args)

    @staticmethod
    def parse_rule() -> parser.SingleResultRule['Args']:
        return (
            '(' &
            (
                Arg.parse_rule() &
                (
                    ',' &
                    Arg.parse_rule()
                )
            ).convert_type(Args).zero_or_one().single_or(Args()) &
            ')'
        ).with_lexer(lexer.Lexer.whitespace())


@dataclass(frozen=True)
class Call(Expr):
    name: str
    args: Args

    @classmethod
    def _parse_rule(cls) -> parser.SingleResultRule[Expr]:
        id_lex_rule = lexer.Rule.load('id', '([a-z]|[A-Z])+')

        class Adapter(parser.SingleResultRule[Expr]):
            def __call__(self, state: tokens.TokenStream, scope: parser.Scope[Expr]) -> parser.StateAndSingleResult[Expr]:
                state, name = parser.Literal(
                    id_lex_rule,
                    lambda token: token.val
                )(state, parser.Scope())
                state, args = Args.parse_rule()(state, parser.Scope())
                return state, Call(name, args)

            @property
            def lexer_(self) -> lexer.Lexer:
                return Args.parse_rule().lexer_ | id_lex_rule

        return Adapter()


def tok(rule_name: str, val: Optional[str] = None) -> tokens.Token:
    return tokens.Token(rule_name, val or rule_name)


def toks(*vals: str | tokens.Token) -> tokens.TokenStream:
    toks: MutableSequence[tokens.Token] = []
    for val in vals:
        if isinstance(val, str):
            val = tok(val)
        toks.append(val)
    return tokens.TokenStream(toks)


class RuleTest(TestCase):
    def test_and(self) -> None:
        no_result_str: str = 'a'
        no_result_lexrule: lexer.Rule = lexer.Rule.load(no_result_str)
        no_result_rule: parser.NoResultRule[Val] = parser.LexRule[Val].load(
            no_result_lexrule)
        single_result_rule: parser.SingleResultRule[Val] = parser.Ref[Val]('a')
        optional_result_rule: parser.OptionalResultRule[Val] = single_result_rule.zero_or_one(
        )
        multiple_result_rule: parser.MultipleResultRule[Val] = single_result_rule.zero_or_more(
        )
        no_result_and: parser.NoResultAnd[Val] = no_result_rule & no_result_rule
        optional_result_and: parser.OptionalResultAnd[Val] = no_result_rule & optional_result_rule
        single_result_and: parser.SingleResultAnd[Val] = no_result_rule & single_result_rule
        multiple_result_and: parser.MultipleResultAnd[Val] = single_result_rule & single_result_rule
        for lhs, rhs, expected in list[tuple[
            Union[
                parser.NoResultRule[Val],
                parser.SingleResultRule[Val],
                parser.MultipleResultRule[Val],
                parser.OptionalResultRule[Val],
            ],
            Union[
                str,
                lexer.Rule,
                parser.NoResultRule[Val],
                parser.SingleResultRule[Val],
                parser.MultipleResultRule[Val],
                parser.OptionalResultRule[Val],
            ],
            parser.Rule[Val],
        ]]([
            # no_result_rule
            (
                no_result_rule,
                no_result_str,
                parser.NoResultAnd([
                    no_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                no_result_rule,
                no_result_lexrule,
                parser.NoResultAnd([
                    no_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                no_result_rule,
                no_result_rule,
                parser.NoResultAnd([
                    no_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                no_result_rule,
                optional_result_rule,
                parser.OptionalResultAnd(
                    list[parser.NoResultRule[Val] | parser.OptionalResultRule[Val]]([
                        no_result_rule,
                        optional_result_rule,
                    ])
                ),
            ),
            (
                no_result_rule,
                single_result_rule,
                parser.SingleResultAnd(
                    list[parser.NoResultRule[Val] | parser.SingleResultRule[Val]]([
                        no_result_rule,
                        single_result_rule,
                    ])
                ),
            ),
            (
                no_result_rule,
                multiple_result_rule,
                parser.MultipleResultAnd([
                    no_result_rule,
                    multiple_result_rule,
                ]),
            ),
            # optional_result_rule
            (
                optional_result_rule,
                no_result_str,
                parser.OptionalResultAnd(
                    list[parser.NoResultRule[Val] | parser.OptionalResultRule[Val]]([
                        optional_result_rule,
                        no_result_rule,
                    ])
                ),
            ),
            (
                optional_result_rule,
                no_result_lexrule,
                parser.OptionalResultAnd(
                    list[parser.NoResultRule[Val] | parser.OptionalResultRule[Val]]([
                        optional_result_rule,
                        no_result_rule,
                    ])
                ),
            ),
            (
                optional_result_rule,
                no_result_rule,
                parser.OptionalResultAnd(
                    list[parser.NoResultRule[Val] | parser.OptionalResultRule[Val]]([
                        optional_result_rule,
                        no_result_rule,
                    ])
                ),
            ),
            (
                optional_result_rule,
                optional_result_rule,
                parser.MultipleResultAnd([
                    optional_result_rule,
                    optional_result_rule,
                ]),
            ),
            (
                optional_result_rule,
                single_result_rule,
                parser.MultipleResultAnd([
                    optional_result_rule,
                    single_result_rule,
                ]),
            ),
            (
                optional_result_rule,
                multiple_result_rule,
                parser.MultipleResultAnd([
                    optional_result_rule,
                    multiple_result_rule,
                ]),
            ),
            # single_result_rule
            (
                single_result_rule,
                no_result_str,
                parser.SingleResultAnd(
                    list[parser.NoResultRule[Val] | parser.SingleResultRule[Val]]([
                        single_result_rule,
                        no_result_rule,
                    ])
                ),
            ),
            (
                single_result_rule,
                no_result_lexrule,
                parser.SingleResultAnd(
                    list[parser.NoResultRule[Val] | parser.SingleResultRule[Val]]([
                        single_result_rule,
                        no_result_rule,
                    ])
                ),
            ),
            (
                single_result_rule,
                no_result_rule,
                parser.SingleResultAnd(
                    list[parser.NoResultRule[Val] | parser.SingleResultRule[Val]]([
                        single_result_rule,
                        no_result_rule,
                    ])
                ),
            ),
            (
                single_result_rule,
                optional_result_rule,
                parser.MultipleResultAnd([
                    single_result_rule,
                    optional_result_rule,
                ]),
            ),
            (
                single_result_rule,
                single_result_rule,
                parser.MultipleResultAnd([
                    single_result_rule,
                    single_result_rule,
                ]),
            ),
            (
                single_result_rule,
                multiple_result_rule,
                parser.MultipleResultAnd([
                    single_result_rule,
                    multiple_result_rule,
                ]),
            ),
            # multiple_result_rule
            (
                multiple_result_rule,
                no_result_str,
                parser.MultipleResultAnd([
                    multiple_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                multiple_result_rule,
                no_result_lexrule,
                parser.MultipleResultAnd([
                    multiple_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                multiple_result_rule,
                no_result_rule,
                parser.MultipleResultAnd([
                    multiple_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                multiple_result_rule,
                optional_result_rule,
                parser.MultipleResultAnd([
                    multiple_result_rule,
                    optional_result_rule,
                ]),
            ),
            (
                multiple_result_rule,
                single_result_rule,
                parser.MultipleResultAnd([
                    multiple_result_rule,
                    single_result_rule,
                ]),
            ),
            (
                multiple_result_rule,
                multiple_result_rule,
                parser.MultipleResultAnd([
                    multiple_result_rule,
                    multiple_result_rule,
                ]),
            ),
            # no_result_and
            (
                no_result_and,
                no_result_str,
                parser.NoResultAnd(
                    list(no_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                no_result_and,
                no_result_lexrule,
                parser.NoResultAnd(
                    list(no_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                no_result_and,
                no_result_rule,
                parser.NoResultAnd(
                    list(no_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                no_result_and,
                optional_result_rule,
                parser.OptionalResultAnd(
                    list(no_result_and) +
                    [
                        optional_result_rule,
                    ]
                ),
            ),
            (
                no_result_and,
                single_result_rule,
                parser.SingleResultAnd(
                    list(no_result_and) +
                    [
                        single_result_rule,
                    ]
                ),
            ),
            (
                no_result_and,
                multiple_result_rule,
                parser.MultipleResultAnd(
                    list(no_result_and) +
                    [
                        multiple_result_rule,
                    ]
                ),
            ),
            # optional_result_and
            (
                optional_result_and,
                no_result_str,
                parser.OptionalResultAnd(
                    list(optional_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                optional_result_and,
                no_result_lexrule,
                parser.OptionalResultAnd(
                    list(optional_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                optional_result_and,
                no_result_rule,
                parser.OptionalResultAnd(
                    list(optional_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                optional_result_and,
                optional_result_rule,
                parser.MultipleResultAnd(
                    list(optional_result_and) +
                    [
                        optional_result_rule,
                    ]
                ),
            ),
            (
                optional_result_and,
                single_result_rule,
                parser.MultipleResultAnd(
                    list(optional_result_and) +
                    [
                        single_result_rule,
                    ]
                ),
            ),
            (
                optional_result_and,
                multiple_result_rule,
                parser.MultipleResultAnd(
                    list(optional_result_and) +
                    [
                        multiple_result_rule,
                    ]
                ),
            ),
            # single_result_and
            (
                single_result_and,
                no_result_str,
                parser.SingleResultAnd(
                    list(single_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                single_result_and,
                no_result_lexrule,
                parser.SingleResultAnd(
                    list(single_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                single_result_and,
                no_result_rule,
                parser.SingleResultAnd(
                    list(single_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                single_result_and,
                optional_result_rule,
                parser.MultipleResultAnd(
                    list(single_result_and) +
                    [
                        optional_result_rule,
                    ]
                ),
            ),
            (
                single_result_and,
                single_result_rule,
                parser.MultipleResultAnd(
                    list(single_result_and) +
                    [
                        single_result_rule,
                    ]
                ),
            ),
            (
                single_result_and,
                multiple_result_rule,
                parser.MultipleResultAnd(
                    list(single_result_and) +
                    [
                        multiple_result_rule,
                    ]
                ),
            ),
            # multiple_result_and
            (
                multiple_result_and,
                no_result_str,
                parser.MultipleResultAnd(
                    list(multiple_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                multiple_result_and,
                no_result_lexrule,
                parser.MultipleResultAnd(
                    list(multiple_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                multiple_result_and,
                no_result_rule,
                parser.MultipleResultAnd(
                    list(multiple_result_and) +
                    [
                        no_result_rule,
                    ]
                ),
            ),
            (
                multiple_result_and,
                optional_result_rule,
                parser.MultipleResultAnd(
                    list(multiple_result_and) +
                    [
                        optional_result_rule,
                    ]
                ),
            ),
            (
                multiple_result_and,
                single_result_rule,
                parser.MultipleResultAnd(
                    list(multiple_result_and) +
                    [
                        single_result_rule,
                    ]
                ),
            ),
            (
                multiple_result_and,
                multiple_result_rule,
                parser.MultipleResultAnd(
                    list(multiple_result_and) +
                    [
                        multiple_result_rule,
                    ]
                ),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                self.assertEqual(lhs & rhs, expected)

    def test_rand(self) -> None:
        no_result_str: str = 'a'
        no_result_lexrule: lexer.Rule = lexer.Rule.load(no_result_str)
        no_result_rule: parser.NoResultRule[Val] = parser.LexRule[Val].load(
            no_result_lexrule)
        single_result_rule: parser.SingleResultRule[Val] = parser.Ref[Val]('a')
        optional_result_rule: parser.OptionalResultRule[Val] = single_result_rule.zero_or_one(
        )
        multiple_result_rule: parser.MultipleResultRule[Val] = single_result_rule.zero_or_more(
        )
        no_result_and: parser.NoResultAnd[Val] = no_result_rule & no_result_rule
        optional_result_and: parser.OptionalResultAnd[Val] = no_result_rule & optional_result_rule
        single_result_and: parser.SingleResultAnd[Val] = no_result_rule & single_result_rule
        multiple_result_and: parser.MultipleResultAnd[Val] = single_result_rule & single_result_rule
        for lhs, rhs, expected in list[tuple[
            Union[
                str,
                lexer.Rule,
            ],
            Union[
                parser.NoResultRule[Val],
                parser.OptionalResultRule[Val],
                parser.SingleResultRule[Val],
                parser.MultipleResultRule[Val],
            ],
            parser.Rule[Val],
        ]]([
            # no_result_rule
            (
                no_result_str,
                no_result_rule,
                parser.NoResultAnd([
                    no_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                no_result_lexrule,
                no_result_rule,
                parser.NoResultAnd([
                    no_result_rule,
                    no_result_rule,
                ]),
            ),
            # optional_result_rule
            (
                no_result_str,
                optional_result_rule,
                parser.OptionalResultAnd(
                    list[parser.NoResultRule[Val] | parser.OptionalResultRule[Val]]([
                        no_result_rule,
                        optional_result_rule,
                    ])
                ),
            ),
            (
                no_result_lexrule,
                optional_result_rule,
                parser.OptionalResultAnd(
                    list[parser.NoResultRule[Val] | parser.OptionalResultRule[Val]]([
                        no_result_rule,
                        optional_result_rule,
                    ])
                ),
            ),
            # single_result_rule
            (
                no_result_str,
                single_result_rule,
                parser.SingleResultAnd(
                    list[parser.NoResultRule[Val] | parser.SingleResultRule[Val]]([
                        no_result_rule,
                        single_result_rule,
                    ])
                ),
            ),
            (
                no_result_lexrule,
                single_result_rule,
                parser.SingleResultAnd(
                    list[parser.NoResultRule[Val] | parser.SingleResultRule[Val]]([
                        no_result_rule,
                        single_result_rule,
                    ])
                ),
            ),
            # multiple_result_rule
            (
                no_result_str,
                multiple_result_rule,
                parser.MultipleResultAnd([
                    no_result_rule,
                    multiple_result_rule,
                ]),
            ),
            (
                no_result_lexrule,
                multiple_result_rule,
                parser.MultipleResultAnd([
                    no_result_rule,
                    multiple_result_rule,
                ]),
            ),
            # no_result_and
            (
                no_result_str,
                no_result_and,
                parser.NoResultAnd(
                    [no_result_rule]
                    + list(no_result_and)
                ),
            ),
            (
                no_result_lexrule,
                no_result_and,
                parser.NoResultAnd(
                    [no_result_rule]
                    + list(no_result_and)
                ),
            ),
            # optional_result_and
            (
                no_result_str,
                optional_result_and,
                parser.OptionalResultAnd(
                    [no_result_rule]
                    + list(optional_result_and)
                ),
            ),
            (
                no_result_lexrule,
                optional_result_and,
                parser.OptionalResultAnd(
                    [no_result_rule]
                    + list(optional_result_and)
                ),
            ),
            # single_result_and
            (
                no_result_str,
                single_result_and,
                parser.SingleResultAnd(
                    [no_result_rule]
                    + list(single_result_and)
                ),
            ),
            (
                no_result_lexrule,
                single_result_and,
                parser.SingleResultAnd(
                    [no_result_rule]
                    + list(single_result_and)
                ),
            ),
            # multiple_result_and
            (
                no_result_str,
                multiple_result_and,
                parser.MultipleResultAnd(
                    [no_result_rule]
                    + list(multiple_result_and)
                ),
            ),
            (
                no_result_lexrule,
                multiple_result_and,
                parser.MultipleResultAnd(
                    [no_result_rule]
                    + list(multiple_result_and)
                ),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                actual = lhs & rhs
                self.assertEqual(
                    actual,
                    expected,
                    f'{lhs} & {rhs} = {actual} != {expected}',
                )

    def test_or(self):
        for lhs, rhs, expected in list[tuple[
            parser.SingleResultRule[Val],
            parser.SingleResultRule[Val],
            parser.SingleResultRule[Val],
        ]]([
            (
                parser.Ref[Val]('a'),
                parser.Ref[Val]('b'),
                parser.Or[Val]([
                    parser.Ref[Val]('a'),
                    parser.Ref[Val]('b'),
                ]),
            ),
            (
                parser.Or[Val]([
                    parser.Ref[Val]('a'),
                    parser.Ref[Val]('b'),
                ]),
                parser.Ref[Val]('c'),
                parser.Or[Val]([
                    parser.Ref[Val]('a'),
                    parser.Ref[Val]('b'),
                    parser.Ref[Val]('c'),
                ]),
            ),
        ]):
            with self.subTest(lhs=lhs, rhs=rhs, expected=expected):
                self.assertEqual(lhs | rhs, expected)

    def test_call(self) -> None:
        load_int: parser.SingleResultRule[Val] = Int._parse_rule()
        load_str: parser.SingleResultRule[Val] = Str._parse_rule()
        parser_: parser.Parser[Val] = Val.parser_()

        for rule, state, scope, expected in list[tuple[
            parser.SingleResultRule[Val],
            tokens.TokenStream,
            parser.Scope[Val],
            Optional[parser.StateAndSingleResult[Val]],
        ]]([
            # literal
            (
                load_int,
                toks(tok('int', '1')),
                parser.Scope[Val](),
                (
                    toks(),
                    Int(1),
                ),
            ),
            (
                load_int,
                toks('a'),
                parser.Scope[Val](),
                None,
            ),
            (
                load_int,
                toks(tok('int', 'a')),
                parser.Scope[Val](),
                None,
            ),
            (
                load_int,
                toks(tok('int', '1'), 'a'),
                parser.Scope[Val](),
                (
                    toks('a'),
                    Int(1),
                ),
            ),
            # ref
            (
                parser.Ref[Val]('a'),
                toks(tok('int', '1')),
                parser.Scope[Val]({
                    'a': load_int,
                }),
                (
                    toks(),
                    Int(1),
                ),
            ),
            (
                parser.Ref[Val]('a'),
                toks(tok('int', '1'), 'b'),
                parser.Scope[Val]({
                    'a': load_int,
                }),
                (
                    toks('b'),
                    Int(1),
                ),
            ),
            # or
            (
                load_int | load_str,
                toks(tok('int', '1')),
                parser.Scope[Val](),
                (
                    toks(),
                    Int(1),
                ),
            ),
            (
                load_int | load_str,
                toks(tok('str', '"a"')),
                parser.Scope[Val](),
                (
                    toks(),
                    Str('a'),
                ),
            ),
            (
                load_int | load_str,
                toks(tok('int', '1'), 'b'),
                parser.Scope[Val](),
                (
                    toks('b'),
                    Int(1),
                ),
            ),
            (
                load_int | load_str,
                toks(tok('str', '"a"'), 'b'),
                parser.Scope[Val](),
                (
                    toks('b'),
                    Str('a'),
                ),
            ),
            (
                load_int | load_str,
                toks('b'),
                parser.Scope[Val](),
                None,
            ),
            # zero_or_more
            (
                load_int.zero_or_more().convert(List),
                toks(),
                parser.Scope[Val](),
                (
                    toks(),
                    List([]),
                ),
            ),
            (
                load_int.zero_or_more().convert(List),
                toks(
                    tok('int', '1'),
                ),
                parser.Scope[Val](),
                (
                    toks(),
                    List([
                        Int(1),
                    ]),
                ),
            ),
            (
                load_int.zero_or_more().convert(List),
                toks(
                    tok('int', '1'),
                    tok('int', '2'),
                ),
                parser.Scope[Val](),
                (
                    toks(),
                    List([
                        Int(1),
                        Int(2),
                    ]),
                ),
            ),
            (
                load_int.zero_or_more().convert(List),
                toks('b'),
                parser.Scope[Val](),
                (
                    toks('b'),
                    List([]),
                ),
            ),
            (
                load_int.zero_or_more().convert(List),
                toks(
                    tok('int', '1'),
                    'b',
                ),
                parser.Scope[Val](),
                (
                    toks('b'),
                    List([
                        Int(1),
                    ]),
                ),
            ),
            (
                load_int.zero_or_more().convert(List),
                toks(
                    tok('int', '1'),
                    tok('int', '2'),
                    'b',
                ),
                parser.Scope[Val](),
                (
                    toks('b'),
                    List([
                        Int(1),
                        Int(2),
                    ]),
                ),
            ),
            # one_or_more
            (
                load_int.one_or_more().convert(List),
                toks(),
                parser.Scope[Val](),
                None,
            ),
            (
                load_int.one_or_more().convert(List),
                toks(
                    tok('int', '1'),
                ),
                parser.Scope[Val](),
                (
                    toks(),
                    List([
                        Int(1),
                    ]),
                ),
            ),
            (
                load_int.one_or_more().convert(List),
                toks(
                    tok('int', '1'),
                    tok('int', '2'),
                ),
                parser.Scope[Val](),
                (
                    toks(),
                    List([
                        Int(1),
                        Int(2),
                    ]),
                ),
            ),
            (
                load_int.one_or_more().convert(List),
                toks('b'),
                parser.Scope[Val](),
                None,
            ),
            (
                load_int.one_or_more().convert(List),
                toks(
                    tok('int', '1'),
                    'b',
                ),
                parser.Scope[Val](),
                (
                    toks('b'),
                    List([
                        Int(1),
                    ]),
                ),
            ),
            (
                load_int.one_or_more().convert(List),
                toks(
                    tok('int', '1'),
                    tok('int', '2'),
                    'b',
                ),
                parser.Scope[Val](),
                (
                    toks('b'),
                    List([
                        Int(1),
                        Int(2),
                    ]),
                ),
            ),
            # zero_or_one
            (
                load_int.zero_or_one().single_or(Int(0)),
                toks(),
                parser.Scope[Val](),
                (
                    toks(),
                    Int(0),
                ),
            ),
            (
                load_int.zero_or_one().single_or(Int(0)),
                toks(
                    tok('int', '1'),
                ),
                parser.Scope[Val](),
                (
                    toks(),
                    Int(1),
                ),
            ),
            (
                load_int.zero_or_one().single_or(Int(0)),
                toks('b'),
                parser.Scope[Val](),
                (
                    toks('b'),
                    Int(0),
                ),
            ),
            (
                load_int.zero_or_one().single_or(Int(0)),
                toks(
                    tok('int', '1'),
                    'b',
                ),
                parser.Scope[Val](),
                (
                    toks('b'),
                    Int(1),
                ),
            ),
            # until_empty
            (
                load_int.until_empty().convert(List),
                toks(),
                parser.Scope[Val](),
                (
                    toks(),
                    List([]),
                ),
            ),
            (
                load_int.until_empty().convert(List),
                toks(
                    tok('int', '1'),
                ),
                parser.Scope[Val](),
                (
                    toks(),
                    List([
                        Int(1),
                    ]),
                ),
            ),
            (
                load_int.until_empty().convert(List),
                toks(
                    tok('int', '1'),
                    tok('int', '2'),
                ),
                parser.Scope[Val](),
                (
                    toks(),
                    List([
                        Int(1),
                        Int(2),
                    ]),
                ),
            ),
            (
                load_int.until_empty().convert(List),
                toks('b'),
                parser.Scope[Val](),
                None,
            ),
            (
                load_int.until_empty().convert(List),
                toks(
                    tok('int', '1'),
                    'b',
                ),
                parser.Scope[Val](),
                None,
            ),
            (
                load_int.until_empty().convert(List),
                toks(
                    tok('int', '1'),
                    tok('int', '2'),
                    'b',
                ),
                parser.Scope[Val](),
                None,
            ),
            # and
            (
                '(' & load_int & ')',
                toks('(', tok('int', '1'), ')'),
                parser.Scope({}),
                (
                    toks(),
                    Int(1),
                ),
            ),
            (
                ('(' & load_int & ',' & load_int & ')').convert(List),
                toks('(', tok('int', '1'), ',', tok('int', '2'), ')'),
                parser.Scope({}),
                (
                    toks(),
                    List([
                        Int(1),
                        Int(2),
                    ]),
                ),
            ),
            # parser
            (
                parser_,
                toks(
                    tok('int', '1'),
                ),
                parser.Scope({}),
                (
                    toks(),
                    Int(1),
                ),
            ),
            (
                parser_,
                toks(
                    tok('str', '"a"'),
                ),
                parser.Scope({}),
                (
                    toks(),
                    Str('a'),
                ),
            ),
            (
                parser_,
                toks(
                    '[',
                    ']',
                ),
                parser.Scope({}),
                (
                    toks(),
                    List([]),
                ),
            ),
            (
                parser_,
                toks(
                    '[',
                    tok('int', '1'),
                    ']',
                ),
                parser.Scope({}),
                (
                    toks(),
                    List([
                        Int(1),
                    ]),
                ),
            ),
            (
                parser_,
                toks(
                    '[',
                    tok('int', '1'),
                    ',',
                    tok('str', '"a"'),
                    ']',
                ),
                parser.Scope({}),
                (
                    toks(),
                    List([
                        Int(1),
                        Str('a'),
                    ]),
                ),
            ),
            (
                parser_,
                toks(
                    '[',
                    tok('int', '1'),
                    ',',
                    tok('int', '2'),
                    ',',
                    tok('int', '3'),
                    ']',
                ),
                parser.Scope({}),
                (
                    toks(),
                    List([
                        Int(1),
                        Int(2),
                        Int(3),
                    ]),
                ),
            ),
            (
                parser_,
                toks(
                    '[',
                    '[',
                    tok('int', '1'),
                    ',',
                    tok('int', '2'),
                    ']',
                    ',',
                    tok('int', '3'),
                    ']',
                ),
                parser.Scope({}),
                (
                    toks(),
                    List([
                        List([
                            Int(1),
                            Int(2),
                        ]),
                        Int(3),
                    ]),
                ),
            ),
            (
                parser.Ref[Val]('a').with_scope(
                    parser.Scope({'a': Val.parser_()})),
                toks(tok('int', '1')),
                parser.Scope(),
                (
                    toks(),
                    Int(1)
                )
            ),
            (
                parser.Ref[Val]('a').zero_or_one().with_scope(
                    parser.Scope({'a': Val.parser_()})).single_or(Int(0)),
                toks(),
                parser.Scope(),
                (
                    toks(),
                    Int(0)
                )
            ),
            (
                parser.Ref[Val]('a').zero_or_one().with_scope(
                    parser.Scope({'a': Val.parser_()})).single_or(Int(0)),
                toks(tok('int', '1')),
                parser.Scope(),
                (
                    toks(),
                    Int(1)
                )
            ),
            (
                parser.Ref[Val]('a').zero_or_more().with_scope(
                    parser.Scope({'a': Val.parser_()})).convert_type(List),
                toks(),
                parser.Scope(),
                (
                    toks(),
                    List([])
                )
            ),
            (
                parser.Ref[Val]('a').zero_or_more().with_scope(
                    parser.Scope({'a': Val.parser_()})).convert_type(List),
                toks(tok('int', '1')),
                parser.Scope(),
                (
                    toks(),
                    List([Int(1)])
                )
            ),
            (
                '{' & Val.parser_() & '}',
                toks(tok('{'), tok('int', '1'), tok('}')),
                parser.Scope(),
                (
                    toks(),
                    Int(1),
                ),
            ),
            (
                '{' & Val.parser_().zero_or_more().convert(List) & '}',
                toks(
                    tok('{'),
                    tok('int', '1'),
                    tok('int', '2'),
                    tok('int', '3'),
                    tok('}'),
                ),
                parser.Scope(),
                (
                    toks(),
                    List([
                        Int(1),
                        Int(2),
                        Int(3),
                    ]),
                ),
            ),
            (
                '{' & Val.parser_().zero_or_more().convert(List) & '}',
                toks(
                    tok('{'),
                    tok('int', '1'),
                    tok('a', '2'),
                    tok('int', '3'),
                    tok('}'),
                ),
                parser.Scope(),
                None,
            ),
            (
                '{' & Val.parser_().until_token('}').convert(List) & '}',
                toks(
                    tok('{'),
                    tok('int', '1'),
                    tok('int', '2'),
                    tok('int', '3'),
                    tok('}'),
                ),
                parser.Scope(),
                (
                    toks(),
                    List([
                        Int(1),
                        Int(2),
                        Int(3),
                    ]),
                ),
            ),
            (
                '{' & Val.parser_().until_token('}').convert(List) & '}',
                toks(
                    tok('{'),
                    tok('int', '1'),
                    tok('a', '2'),
                    tok('int', '3'),
                    tok('}'),
                ),
                parser.Scope(),
                None,
            ),
        ]):
            with self.subTest(rule=rule, state=state, scope=scope, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        rule(state, scope)
                else:
                    self.assertEqual(rule(state, scope), expected)

    def test_convert_type(self):
        for rule, input, expected in list[tuple[parser.SingleResultRule[Expr], tokens.TokenStream | str, Expr]]([
            (
                Expr.parser_(),
                toks(tok('int', '1')),
                Literal(Int(1)),
            ),
            (
                Val.parser_().zero_or_one().convert_type(lambda val: Literal(val or Int(0))),
                toks(),
                Literal(Int(0)),
            ),
            (
                Val.parser_().zero_or_one().convert_type(lambda val: Literal(val or Int(0))),
                toks(tok('int', '1')),
                Literal(Int(1)),
            ),
            (
                Val.parser_().zero_or_more().convert_type(lambda vals: Literal(List(vals))),
                toks(),
                Literal(List([])),
            ),
            (
                Val.parser_().zero_or_more().convert_type(lambda vals: Literal(List(vals))),
                toks(
                    tok('int', '1'),
                    tok('int', '2'),
                    tok('int', '3'),
                ),
                Literal(List([
                    Int(1),
                    Int(2),
                    Int(3),
                ])),
            ),
            (
                Expr.parser_(),
                '1',
                Literal(Int(1)),
            ),
            (
                Expr.parser_(),
                '"a"',
                Literal(Str('a')),
            ),
        ]):
            with self.subTest(state=input, expected=expected):
                state, expr = rule.eval(input)
                self.assertEqual(state, toks())
                self.assertEqual(expr, expected)

    def test_with_lexer(self):
        lex_rule_a = lexer.Rule.load('a')
        lexer_a = lexer.Lexer([lex_rule_a])
        lex_rule_b = lexer.Rule.load('b')
        lexer_b = lexer.Lexer([lex_rule_b])
        for rule, lexer_, expected in list[tuple[
            Union[
                parser.NoResultRule[Val],
                parser.SingleResultRule[Val],
                parser.OptionalResultRule[Val],
                parser.MultipleResultRule[Val],
            ],
            lexer.Lexer,
            lexer.Lexer,
        ]]([
            (
                parser.LexRule(lex_rule_a),
                lexer.Lexer(),
                lexer_a,
            ),
            (
                parser.LexRule(lex_rule_a),
                lexer_b,
                lexer_a | lexer_b,
            ),
            (
                Val.ref(),
                lexer.Lexer(),
                lexer.Lexer(),
            ),
            (
                Val.ref(),
                lexer_a,
                lexer_a,
            ),
            (
                Val.ref().zero_or_one(),
                lexer.Lexer(),
                lexer.Lexer(),
            ),
            (
                Val.ref().zero_or_one(),
                lexer_a,
                lexer_a,
            ),
            (
                Val.ref().zero_or_more(),
                lexer.Lexer(),
                lexer.Lexer(),
            ),
            (
                Val.ref().zero_or_more(),
                lexer_a,
                lexer_a,
            ),
            (
                Int._parse_rule(),
                lexer.Lexer(),
                Int._parse_rule().lexer_,
            ),
            (
                Int._parse_rule(),
                lexer.Lexer([lex_rule_a]),
                Int._parse_rule().lexer_ | lexer.Lexer([lex_rule_a]),
            ),
        ]):
            with self.subTest(rule=rule, lexer_=lexer_, expected=expected):
                self.assertEqual(
                    rule.with_lexer(lexer_).lexer_,
                    expected
                )
