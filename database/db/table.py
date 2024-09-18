from typing import List
from dataclasses import dataclass

from database.db.value import Value
from database.constants import ValueType


@dataclass
class Record:
  values: List[Value]

  def __getitem__(self, key: str) -> Value:
    for v in self.values:
      if v.name == key:
        return v
    raise KeyError(key)

  def __contains__(self, key: str) -> bool:
    for v in self.values:
      if v.name == key:
        return True
    return False

  def add_text(self, name: str, text: str) -> "Record":
    self.values.append(Value.from_text(text, name))
    return self

  def add_integer(self, name: str, integer: int) -> "Record":
    self.values.append(Value.from_integer(integer, name))
    return self


@dataclass
class Table:
  records: List[Record]


@dataclass
class Index:
  column: str
  prefix: int = 0


@dataclass
class TableDef:
  name: str
  columns: List[str]
  column_types: List[ValueType]
  primary_index: Index
  indexes: List[Index]

  def to_dict(self) -> dict:
    return {
        "name": self.name,
        "columns": self.columns,
        "column_types": [x.value for x in self.column_types],
        "primary_index": {
            "column": self.primary_index.column,
            "prefix": self.primary_index.prefix,
        },
        "indexes": [
            {"column": i.column, "prefix": i.prefix} for i in self.indexes
        ],
    }

  @staticmethod
  def from_dict(data: dict) -> "TableDef":
    return TableDef(
        data["name"],
        data["columns"],
        [ValueType(x) for x in data["column_types"]],
        Index(data["primary_index"]["column"], data["primary_index"]["prefix"]),
        [Index(i["column"], i["prefix"]) for i in data["indexes"]],
    )

  def validate(self):
    if len(self.columns) != len(self.column_types):
      raise ValueError(
          "columns and column_types must have the same length"
      )
    if len(self.columns) != len(set(self.columns)):
      raise ValueError("columns must be unique")
    for field in self.column_types:
      if field not in [ValueType.TEXT, ValueType.INTEGER]:
        raise ValueError("Invalid column type")
    if self.primary_index.column in [x.column for x in self.indexes]:
      raise ValueError("primary index column cannot be in indexes")
    for index in [self.primary_index, *self.indexes]:
      if index.prefix != 0:
        raise ValueError("index prefix must be 0")
      if index.column not in self.columns:
        raise ValueError(f"{index.column} not found in columns")

  def validate_record(self, record: Record) -> Record:
    for v in record.values:
      if v.name not in self.columns:
        raise ValueError(f"{v.name} not found in columns")
    new_rec = Record([])
    for column, tp in zip(self.columns, self.column_types):
      if column not in record:
        raise ValueError(f"{column} not found in record")
      if ValueType(tp) != record[column].type:
        raise ValueError(f"Invalid type for {column}")
      new_rec.values.append(record[column])
    return new_rec

  def get_column_type(self, column: str) -> ValueType:
    for c, t in zip(self.columns, self.column_types):
      if c == column:
        return t
    raise ValueError(f"{column} not found in columns")

  def find_index(self, column: str) -> Index:
    if column not in self.columns:
      raise ValueError(f"{column} not found in columns")
    for index in [self.primary_index, *self.indexes]:
      if index.column == column:
        return index
    raise ValueError(f"{column} not found in indexes")


TDEF_META = TableDef(
    "@meta",
    ["key", "value"],
    [ValueType.TEXT, ValueType.TEXT],
    Index("key", 1),
    [],
)

TDEF_TABLES = TableDef(
    "@tables",
    ["name", "def"],
    [ValueType.TEXT, ValueType.TEXT],
    Index("name", 2),
    [],
)
