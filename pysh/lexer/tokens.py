from ..regex.chars import *
from ..errors import *
from .. import regex


@dataclass(frozen=True)
class Token:
    rule_name: str
    val: str
    position: Position = field(
        default_factory=Position, compare=False, repr=False)

    @staticmethod
    def load(rule_name: str, chars: Sequence[Char] | CharStream | regex.Result) -> 'Token':
        if isinstance(chars, CharStream):
            return Token.load(rule_name, chars.chars)
        if isinstance(chars, regex.Result):
            return Token.load(rule_name, chars.chars_)
        if not chars:
            raise Error(msg='no chars to load token')
        return Token(rule_name, ''.join(char.val for char in chars), chars[0].position)


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

    @staticmethod
    def concat(streams: Sequence['TokenStream']) -> 'TokenStream':
        return TokenStream(sum((list(stream.tokens) for stream in streams), list[Token]()))

    def head(self) -> Token:
        if not self:
            raise Error(msg='head from empty tokenstream')
        return self.tokens[0]

    def tail(self) -> 'TokenStream':
        if not self:
            raise Error(msg='tail from empty tokenstream')
        return TokenStream(self.tokens[1:])
