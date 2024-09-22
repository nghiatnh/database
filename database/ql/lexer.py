from typing import Optional

from database.ql.exceptions import QLError
from database.ql.token import Token
from database.ql.constants import TokenType
from database.ql.constants import PUNCTUATIONS
from database.ql.constants import OPERATORS1CHAR
from database.ql.constants import OPERATORS2CHAR
from database.ql.constants import KEYWORDS


class Lexer:
  """
  Lexer
  =====
  Lexer class represents a lexer that tokenizes the source code. It contains the
  source code and the current position in the source code.
  """

  def __init__(
      self,
      text: str,
  ):
    self._text = text
    self._pos = 0
    self._line = 1
    self._column = 1

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  @property
  def _is_eof(self) -> bool:
    return self._pos >= len(self._text)

  @property
  def _next_char(self) -> Optional[str]:
    next_pos = self._pos + 1
    return self._text[next_pos] if next_pos < len(self._text) else None

  def _error(
      self,
      line: int,
      column: int,
      message: str = "",
  ) -> QLError:
    return QLError(self._text, line, column, message)

  def _move_next(self):
    if not self._is_eof:
      if self.cur_char == "\n":
        self._line += 1
        self._column = 1
        self._pos += 1
      else:
        self._pos += 1
        self._column += 1

  def _skip_whitespace(self):
    while self.cur_char is not None and self.cur_char.isspace():
      self._move_next()

  def _skip_comment(self):
    while (self.cur_char is not None and
           self.cur_char != TokenType.NEWLINE.value):
      self._move_next()
    self._move_next()

  def _number(self) -> int:
    cur = ""
    while self.cur_char is not None and self.cur_char.isdigit():
      cur += self.cur_char
      self._move_next()
    return int(cur)

  def _string(self) -> str:
    cur = ""
    save = (self._line, self._column - 1)
    while not self._is_eof and self.cur_char != TokenType.SINGLE_QUOTE.value:
      assert self.cur_char is not None
      cur += self.cur_char
      self._move_next()
    if self.cur_char is None:
      raise self._error(*save, "Unclosed quote")
    self._move_next()
    return cur

  def _identifier(self) -> str:
    cur = ""
    while (
        self.cur_char is not None and
        (self.cur_char.isalnum() or self.cur_char == "_")
    ):
      cur += self.cur_char
      self._move_next()
    return cur

  def _alpha(self) -> Token:
    line, column = self._line, self._column
    _id = self._identifier()
    upper = _id.upper()
    if upper in KEYWORDS:
      return Token(line, column, KEYWORDS[upper], _id)
    return Token(line, column, TokenType.ID, _id)

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def cur_char(self) -> Optional[str]:
    """
    Get the current character from the source code.
    """
    if self._is_eof:
      return None
    cur_char = self._text[self._pos]
    return cur_char

  @property
  def text(self) -> str:
    """
    Get the source code.
    """
    return self._text

  def next_token(self) -> Token:
    """
    Get the next token from the source code.
    """
    while self.cur_char is not None:
      if self.cur_char.isspace():
        self._skip_whitespace()
        continue

      if (self.cur_char == TokenType.MINUS.value and
              self._next_char == TokenType.MINUS.value):
        self._skip_comment()
        continue

      cur_char = self.cur_char
      line, column = self._line, self._column

      if cur_char == TokenType.SINGLE_QUOTE.value:
        self._move_next()
        return Token(line, column, TokenType.VALUE, self._string())

      if self.cur_char.isdigit():
        return Token(line, column, TokenType.VALUE, self._number())

      # Must check 2 chars before punctuations to avoid ambiguity
      if (self._next_char is not None and
              cur_char + self._next_char in OPERATORS2CHAR):
        cur_char += self._next_char
        self._move_next()
        self._move_next()
        return Token(line, column, OPERATORS2CHAR[cur_char], cur_char)

      if cur_char in PUNCTUATIONS:
        self._move_next()
        return Token(line, column, PUNCTUATIONS[cur_char], cur_char)

      if cur_char in OPERATORS1CHAR:
        self._move_next()
        return Token(line, column, OPERATORS1CHAR[cur_char], cur_char)

      if cur_char.isalpha():
        return self._alpha()

      raise self._error(
          self._line, self._column, f"Invalid character {cur_char}")

    return Token(self._line, self._column, TokenType.EOF)
