from dataclasses import dataclass, field
from typing import Iterable, Iterator, MutableSequence, Optional, Sequence, Sized
from . import errors


@dataclass(frozen=True)
class Position:
    line: int = 0
    col: int = 0

    def __str__(self) -> str:
        return f'({self.line},{self.col})'

    def __add__(self, char: 'Char') -> 'Position':
        if char.val == '\n':
            return Position(self.line+1, 0)
        else:
            return Position(self.line, self.col+1)


@dataclass(frozen=True)
class Char:
    val: str
    position: Position = field(
        default_factory=Position)

    def __str__(self) -> str:
        return self.val

    def __post_init__(self):
        if len(self.val) != 1:
            raise errors.Error(msg=f'invalid char {self}')


@dataclass(frozen=True)
class CharStream(Sized, Iterable[Char]):
    chars: Sequence[Char] = field(default_factory=list[Char])

    def __str__(self) -> str:
        if self:
            return f"CharStream({''.join([char.val for char in self.chars])}@{self.head().position})"
        else:
            return 'CharStream()'

    def __bool__(self) -> bool:
        return bool(self.chars)

    def __iter__(self) -> Iterator[Char]:
        return iter(self.chars)

    def __len__(self) -> int:
        return len(self.chars)

    def head(self) -> Char:
        if not self:
            raise errors.Error(msg='head of empty state')
        return self.chars[0]

    def tail(self) -> 'CharStream':
        if not self:
            raise errors.Error(msg='tail of empty state')
        return CharStream(self.chars[1:])

    @staticmethod
    def load(s: str, starting_position: Optional[Position] = None):
        chars: MutableSequence[Char] = []
        position: Position = starting_position or Position()
        for c in s:
            char = Char(c, position)
            chars.append(char)
            position += char
        return CharStream(chars)
