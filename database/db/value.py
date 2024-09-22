from typing import Union
from dataclasses import dataclass

from database.utils import binary
from database.constants import ValueType


@dataclass
class Value:
  """
  Value
  =====
  Value class represents a value in the database.
  """

  type: ValueType
  data: bytes
  name: str

  def __repr__(self) -> str:
    return f"{self.type.name}({self.name}={self.value})"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def text(self) -> str:
    """
    Return the value as a string.
    """
    assert self.type == ValueType.TEXT
    return self.data.decode("utf-8")

  @property
  def integer(self) -> int:
    """
    Return the value as an integer.
    """
    assert self.type == ValueType.INTEGER
    return binary.int64(self.data, order="big")

  @property
  def value(self) -> Union[str, int]:
    """
    Return the value as either a string or an integer.
    """
    if self.type == ValueType.TEXT:
      return self.text
    return self.integer

  @staticmethod
  def empty(value_type: ValueType, name: str = "") -> "Value":
    """
    Create an empty value for the given type and name.
    """
    if value_type == ValueType.TEXT:
      return Value(ValueType.TEXT, b"", name)
    return Value(ValueType.INTEGER, b"", name)

  @staticmethod
  def from_text(text: str, name: str = "") -> "Value":
    """
    Create a value from a text and name.
    """
    return Value(ValueType.TEXT, text.encode("utf-8"), name)

  @staticmethod
  def from_integer(integer: int, name: str = "") -> "Value":
    """
    Create a value from an integer and name.
    """
    return Value(ValueType.INTEGER, binary.bytes8(integer, order="big"), name)
