from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional, Sequence, Sized
from . import chars, errors


@dataclass(frozen=True)
class Token:
    rule_name: str
    val: str
    position: chars.Position = field(default_factory=chars.Position)

    def __str__(self) -> str:
        if self.rule_name == self.val:
            return repr(self.rule_name)
        else:
            return f'{self.rule_name}({repr(str(self.val))})'

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

    def __str__(self) -> str:
        return f"[{', '.join(map(str,self.tokens))}]"

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
            raise TokenStreamError(
                state=self, msg='unexpected end of stream')
        return self.tokens[0]

    def tail(self) -> 'TokenStream':
        stream, _ = self.pop()
        return stream

    def pop(self, rule_name: Optional[str] = None) -> tuple['TokenStream', Token]:
        if not self:
            raise TokenStreamError(state=self, msg='unexpected end of stream')
        if rule_name is not None and self.head().rule_name != rule_name:
            raise TokenStreamError(state=self,
                                   msg=f'got {self.head()} expected {rule_name}')
        return TokenStream(self.tokens[1:]), self.head()


@dataclass(frozen=True, kw_only=True, repr=False)
class TokenStreamError(errors.Error):
    state: TokenStream

    def _repr_line(self) -> str:
        return f'TokenStreamError(state={self.state},msg={repr(self.msg)})'

    def __repr__(self) -> str:
        return self._repr(0)
