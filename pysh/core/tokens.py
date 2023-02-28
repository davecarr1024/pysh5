from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional, Sequence, Sized
from . import chars, errors


@dataclass(frozen=True)
class Token:
    rule_name: str
    val: str
    position: chars.Position = field(default_factory=chars.Position)

    @staticmethod
    def load(rule_name: str, val: Sequence[chars.Char] | chars.CharStream) -> 'Token':
        if isinstance(val, chars.CharStream):
            return Token.load(rule_name, val.chars)
        if not val:
            raise errors.Error(msg='no chars to load token')
        return Token(rule_name, ''.join(char.val for char in val), val[0].position)


@dataclass(frozen=True)
class TokenStream(Sized, Iterable[Token]):
    tokens: Sequence[Token] = field(default_factory=list[Token])

    def __bool__(self) -> bool:
        return bool(self.tokens)

    def __iter__(self) -> Iterator[Token]:
        return iter(self.tokens)

    def __len__(self) -> int:
        return len(self.tokens)

    def __add__(self, rhs: 'TokenStream') -> 'TokenStream':
        return TokenStream(list(self.tokens)+list(rhs.tokens))

    def head(self) -> Token:
        if not self:
            raise errors.Error(msg='head from empty tokenstream')
        return self.tokens[0]

    def tail(self) -> 'TokenStream':
        stream, _ = self.pop()
        return stream

    def pop(self, rule_name: Optional[str] = None) -> tuple['TokenStream', Token]:
        if not self:
            raise errors.Error(msg='pop empty token stream')
        if rule_name is not None and self.head().rule_name != rule_name:
            raise errors.Error(
                msg=f'popping token stream got head {self.head().rule_name} expected {rule_name}')
        return TokenStream(self.tokens[1:]), self.head()
