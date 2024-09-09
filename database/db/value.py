from dataclasses import dataclass

from database.constants import ColumnType


@dataclass
class Value:
  type: ColumnType
  _bytes: bytes = b""
  _int: int = 0

  def __repr__(self) -> str:
    return str(self._bytes if self.type == ColumnType.BYTES else self._int)

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def integer(self) -> int:
    if self.type != ColumnType.INT:
      raise ValueError("Not an integer")
    return self._int

  @property
  def string(self) -> str:
    if self.type != ColumnType.BYTES:
      raise ValueError("Not a string")
    return self._bytes.decode("utf-8")

  @property
  def bytes_(self) -> bytes:
    if self.type != ColumnType.BYTES:
      raise ValueError("Not bytes")
    return self._bytes
