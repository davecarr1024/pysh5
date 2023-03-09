from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import MutableSequence, Optional, Sequence, Union
from unittest import TestCase
from . import errors, lexer, parser, tokens

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    __import__('sys').modules['unittest.util']._MAX_LENGTH = 999999999


class Val:
    ...


@dataclass(frozen=True)
class Int(Val):
    val: int


@dataclass(frozen=True)
class Str(Val):
    val: str


@dataclass(frozen=True)
class List(Val):
    vals: Sequence[Val]


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
    def test_and(self):
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
                parser.OptionalResultAnd([
                    no_result_rule,
                    optional_result_rule,
                ]),
            ),
            (
                no_result_rule,
                single_result_rule,
                parser.SingleResultAnd([
                    no_result_rule,
                    single_result_rule,
                ]),
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
                parser.OptionalResultAnd([
                    optional_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                optional_result_rule,
                no_result_lexrule,
                parser.OptionalResultAnd([
                    optional_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                optional_result_rule,
                no_result_rule,
                parser.OptionalResultAnd([
                    optional_result_rule,
                    no_result_rule,
                ]),
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
                parser.SingleResultAnd([
                    single_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                single_result_rule,
                no_result_lexrule,
                parser.SingleResultAnd([
                    single_result_rule,
                    no_result_rule,
                ]),
            ),
            (
                single_result_rule,
                no_result_rule,
                parser.SingleResultAnd([
                    single_result_rule,
                    no_result_rule,
                ]),
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

    def test_rand(self):
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
                parser.OptionalResultAnd([
                    no_result_rule,
                    optional_result_rule,
                ]),
            ),
            (
                no_result_lexrule,
                optional_result_rule,
                parser.OptionalResultAnd([
                    no_result_rule,
                    optional_result_rule,
                ]),
            ),
            # single_result_rule
            (
                no_result_str,
                single_result_rule,
                parser.SingleResultAnd([
                    no_result_rule,
                    single_result_rule,
                ]),
            ),
            (
                no_result_lexrule,
                single_result_rule,
                parser.SingleResultAnd([
                    no_result_rule,
                    single_result_rule,
                ]),
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

    def test_call(self):
        def convert_int_tok(token: tokens.Token) -> Int:
            try:
                return Int(int(token.val))
            except ValueError as error:
                raise errors.Error(
                    msg=f'failed to convert int token {token}: {error}')

        load_int: parser.SingleResultRule[Val] = parser.Literal[Val](
            lexer.Rule.load('int', '\\d+'),
            convert_int_tok,
        )

        load_str: parser.SingleResultRule[Val] = parser.Literal[Val](
            lexer.Rule.load('str', '"(^")*"'),
            lambda token: Str(token.val[1:-1]),
        )

        load_list: parser.SingleResultRule[Val] = (
            '[' &
            (
                parser.Ref[Val]('val') &
                (
                    ',' &
                    parser.Ref[Val]('val')
                ).zero_or_more()
            ).convert(List).zero_or_one().single_or(List([])) &
            ']'
        )

        parser_ = parser.Parser(
            'val',
            parser.Scope[Val]({
                'val': (
                    parser.Ref[Val]('int') |
                    parser.Ref[Val]('str') |
                    parser.Ref[Val]('list')
                ),
                'int': load_int,
                'str': load_str,
                'list': load_list,
            })
        )

        for rule, state, scope, expected in list[tuple[
            parser.SingleResultRule[Val],
            tokens.TokenStream,
            parser.Scope[Val],
            Optional[parser.StateAndResult[Val]],
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
        ]):
            with self.subTest(rule=rule, state=state, scope=scope, expected=expected):
                if expected is None:
                    with self.assertRaises(errors.Error):
                        rule(state, scope)
                else:
                    self.assertEqual(rule(state, scope), expected)
