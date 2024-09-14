from typing import Union
from dataclasses import dataclass

from database.constants import ColumnType


@dataclass
class Value:
  """
  Value
  =====
  Value class represents a value in the database. It can be either an integer
  or a string. The class provides methods to get the value as an integer or a
  string.
  """

  type: ColumnType
  _bytes: bytes = b""
  _int: int = 0

  def __repr__(self) -> str:
    return str(self._bytes if self.type == ColumnType.BYTES else self._int)

  def __str__(self) -> str:
    return self.__repr__()

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def value(self) -> Union[int, str]:
    """
    Returns the value as an integer or a string.
    """
    if self.type == ColumnType.INT:
      return self.integer
    return self.string

  @property
  def integer(self) -> int:
    """
    Returns the value as an integer.
    """
    if self.type != ColumnType.INT:
      raise ValueError("Not an integer")
    return self._int

  @property
  def string(self) -> str:
    """
    Returns the value as a string.
    """
    if self.type != ColumnType.BYTES:
      raise ValueError("Not a string")
    return self._bytes.decode("utf-8")

  @property
  def bytes_(self) -> bytes:
    """
    Returns the value as bytes.
    """
    if self.type != ColumnType.BYTES:
      raise ValueError("Not bytes")
    return self._bytes
