from typing import List, Optional, Dict
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
    raise KeyError(f"Column not found {column}")

  def __getitem__(self, column: str) -> Value:
    for col, val in zip(self.columns, self.values):
      if col.name == column:
        return val
    raise KeyError(f"Column not found {column}")

  def _validate_column(self, column: str):
    if column in self.column_names:
      raise KeyError("Column existed")

  @staticmethod
  def _format_string(string: str) -> str:
    max_len = 10
    if len(string) < max_len:
      return string + " " * (max_len - len(string))
    return string[:max_len - 3] + "..."

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

  def select(self, aliases: Dict[str, str]) -> "Record":
    """
    Selects columns from the record using aliases.
    """
    columns = []
    values = []
    for field, alias in aliases.items():
      col_idx = self.column_names.index(field)
      columns.append(Column(alias, self.columns[col_idx].type))
      values.append(self.values[col_idx])
    self.columns = columns
    self.values = values
    return self

  @staticmethod
  def format_records(recs: List["Record"]) -> str:
    """
    Formats the records in a table format.
    """
    if not recs:
      return "# No record found"
    res = "‖ " + " ‖ ".join(
        [Record._format_string(x) for x in recs[0].column_names]
    ) + "‖"
    line1 = "\n" + "-" * len(res) + "\n"
    line2 = "\n" + "=" * len(res) + "\n"
    rec_str = "record" if len(recs) == 1 else "records"
    res = f"# {len(recs)} {rec_str} found" + line2 + res + line2
    for rec in recs:
      res += "| " + " | ".join(
          [Record._format_string(str(rec[x].value)) for x in rec.column_names]
      ) + "|"
      res += line1
    return res
