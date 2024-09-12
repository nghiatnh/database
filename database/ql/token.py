from typing import Optional, Union

from database.ql.constants import TokenType


class Token:
  """
  Token
  =====
  Token class represents a token in the source code. It contains the token
  type, value, line, and column where the token was found in the source code.
  """

  def __init__(
      self,
      line: int,
      column: int,
      token_type: TokenType,
      value: Optional[Union[int, bool, str]] = None
  ):
    self.line = line
    self.column = column
    self.type = token_type
    self.value = value

  def __repr__(self) -> str:
    if self.value is None:
      return f"<Token {self.type.name}, {self.line}, {self.column}>"
    return f"<Token {self.type.name}, {self.line}, {self.column}>: {self.value}"

  def __str__(self) -> str:
    return self.__repr__()
