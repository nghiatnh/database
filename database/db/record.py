from typing import List, Optional
from dataclasses import dataclass

from database.db.value import Value
from database.constants import ColumnType


@dataclass
class Column:
  """
  Column
  ======
  Column class represents a column in the database. It contains the name of the
  column and the type of the column.
  """

  name: str
  type: ColumnType

  def __repr__(self) -> str:
    return f"Column({self.name}: {self.type.name})"

  def __str__(self) -> str:
    return self.__repr__()


class Record:
  """
  Record
  ======
  Record class represents a record in the database. It contains the columns and
  values of the record. The class provides methods to add columns and values to
  the record.
  """

  def __init__(
      self,
      *,
      columns: Optional[List[Column]] = None,
      values: Optional[List[Value]] = None,
  ):
    self.columns: List[Column] = columns or []
    self.values: List[Value] = values or []

  def __repr__(self) -> str:
    data_str = ", ".join(
        f"{col.name}={val}" for col, val in zip(self.columns, self.values)
    )
    return f"Record({data_str})"

  def __str__(self) -> str:
    return self.__repr__()

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

  def _validate_column(self, column: str):
    if column in self.column_names:
      raise KeyError("Column existed")

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def n_cols(self) -> int:
    """
    Returns the number of columns in the record.
    """
    return len(self.columns)

  @property
  def column_names(self) -> List[str]:
    """
    Returns the names of the columns in the record.
    """
    return [x.name for x in self.columns]

  def add_string(self, column: str, value: str) -> "Record":
    """
    Adds a string value to the record.
    """
    return self.add_bytes(column, value.encode("utf-8"))

  def add_bytes(self, column: str, value: bytes) -> "Record":
    """
    Adds a bytes value to the record.
    """
    self._validate_column(column)
    self.columns.append(Column(column, ColumnType.BYTES))
    self.values.append(Value(ColumnType.BYTES, value, 0))
    return self

  def add_int(self, column: str, value: int) -> "Record":
    """
    Adds an integer value to the record.
    """
    self._validate_column(column)
    self.columns.append(Column(column, ColumnType.INT))
    self.values.append(Value(ColumnType.INT, b"", value))
    return self
