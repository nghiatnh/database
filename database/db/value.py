from typing import Union
from dataclasses import dataclass

from database.utils import binary
from database.constants import ValueType


@dataclass
class Value:
  type: ValueType
  data: bytes
  name: str

  def __repr__(self) -> str:
    return f"{self.type.name}({self.name}={self.value})"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def text(self) -> str:
    assert self.type == ValueType.TEXT
    return self.data.decode("utf-8")

  @property
  def integer(self) -> int:
    assert self.type == ValueType.INTEGER
    return binary.int64(self.data, order="big")

  @property
  def value(self) -> Union[str, int]:
    if self.type == ValueType.TEXT:
      return self.text
    return self.integer

  @staticmethod
  def from_text(text: str, name: str = "") -> "Value":
    return Value(ValueType.TEXT, text.encode("utf-8"), name)

  @staticmethod
  def from_integer(integer: int, name: str = "") -> "Value":
    return Value(ValueType.INTEGER, binary.bytes8(integer, order="big"), name)
