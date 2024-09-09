from typing import List, Optional
from dataclasses import dataclass

from database.db.value import Value
from database.constants import ColumnType


@dataclass
class Column:
  name: str
  type: ColumnType


class Record:
  def __init__(
      self,
      *,
      columns: Optional[List[Column]] = None,
      values: Optional[List[Value]] = None,
  ) -> None:
    self.columns: List[Column] = columns or []
    self.values: List[Value] = values or []

  def __repr__(self) -> str:
    data_str = ", ".join(
        f"{col.name}={val}" for col, val in zip(self.columns, self.values)
    )
    return f"Record({data_str})"

  def __str__(self) -> str:
    return self.__repr__()

  def _validate_column(self, column: str):
    if column in self.column_names:
      raise KeyError("Column existed")

  @property
  def n_cols(self) -> int:
    return len(self.columns)

  @property
  def column_names(self) -> List[str]:
    return [x.name for x in self.columns]

  def __setitem__(self, column: str, value: Value):
    for i, col in enumerate(self.columns):
      if col.name == column:
        assert value.type == col.type
        self.values[i] = value
        return
    raise KeyError("Column not found")

  def __getitem__(self, column: str) -> Value:
    for col, val in zip(self.columns, self.values):
      if col.name == column:
        return val
    raise KeyError("Column not found")

  def add_string(self, column: str, value: str) -> "Record":
    return self.add_bytes(column, value.encode("utf-8"))

  def add_bytes(self, column: str, value: bytes) -> "Record":
    self._validate_column(column)
    self.columns.append(Column(column, ColumnType.BYTES))
    self.values.append(Value(ColumnType.BYTES, value, 0))
    return self

  def add_int(self, column: str, value: int) -> "Record":
    self._validate_column(column)
    self.columns.append(Column(column, ColumnType.INT))
    self.values.append(Value(ColumnType.INT, b"", value))
    return self
