from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import json

from database.kvstore import KVStore
from database.utils import binary


class UpdateMode(Enum):
  INSERT_ONLY = 1
  UPDATE_ONLY = 2
  UPSERT = 3


class ColumnType(Enum):
  ERROR = 0
  BYTES = 1
  INT = 2


@dataclass
class Value:
  type: ColumnType
  _bytes: bytes
  _int: int

  @property
  def integer(self) -> int:
    if self.type != ColumnType.INT:
      raise ValueError('Not an integer')
    return self._int

  @property
  def string(self) -> str:
    if self.type != ColumnType.BYTES:
      raise ValueError('Not a string')
    return self._bytes.decode('utf-8')

  @property
  def bytes_(self) -> bytes:
    if self.type != ColumnType.BYTES:
      raise ValueError('Not bytes')
    return self._bytes

  def set_int(self, value: int) -> None:
    self._int = value
    self.type = ColumnType.INT

  def set_bytes(self, value: bytes) -> None:
    self._bytes = value
    self.type = ColumnType.BYTES

  def set_string(self, value: str) -> None:
    self._bytes = value.encode('utf-8')
    self.type = ColumnType.BYTES


@dataclass
class Column:
  name: str
  type: ColumnType


class Record:
  def __init__(self) -> None:
    self.columns: List[Column] = []
    self.values: List[Value] = []

  def __repr__(self) -> str:
    return ("Record(" +
            ", ".join(
                f"{col.name}={val.integer if col.type == ColumnType.INT else val.string}"
                for col, val in zip(self.columns, self.values)
            ) + ")")

  def set_value(self, column: str, value: Value):
    for i, col in enumerate(self.columns):
      if col.name == column:
        assert value.type == col.type
        self.values[i] = value
        return
    raise KeyError("Invalid column")

  def add_str(self, column: str, value: str) -> "Record":
    return self.add_bytes(column, value.encode('utf-8'))

  def add_bytes(self, column: str, value: bytes) -> "Record":
    self.columns.append(Column(column, ColumnType.BYTES))
    self.values.append(Value(ColumnType.BYTES, value, 0))
    return self

  def add_int(self, column: str, value: int) -> "Record":
    self.columns.append(Column(column, ColumnType.INT))
    self.values.append(Value(ColumnType.INT, b'', value))
    return self

  def get(self, column: str) -> Value:
    for col, val in zip(self.columns, self.values):
      if col.name == column:
        return val
    raise ValueError('Column not found')


@dataclass
class TableDef:
  name: str
  columns: List[Column]
  pkeys: int
  prefix: int

  @property
  def n_columns(self) -> int:
    return len(self.columns)

  @staticmethod
  def from_dict(data: dict) -> "TableDef":
    return TableDef(
        data["name"],
        [Column(x["name"], ColumnType(x["type"])) for x in data["columns"]],
        data["pkeys"],
        data["prefix"],
    )

  def to_dict(self) -> dict:
    return {
        "name": self.name,
        "columns": [{
            "name": x.name,
            "type": x.type.value,
        } for x in self.columns],
        "pkeys": self.pkeys,
        "prefix": self.prefix,
    }


TDEF_META = TableDef(
    name='@meta',
    columns=[
        Column("key", ColumnType.BYTES), Column("value", ColumnType.BYTES)
    ],
    pkeys=1,
    prefix=1,
)

TDEF_TABLE = TableDef(
    name='@table',
    columns=[Column("name", ColumnType.BYTES), Column("def", ColumnType.BYTES)],
    pkeys=1,
    prefix=2,
)


class Database:
  def __init__(self, path: str) -> None:
    self.path = path
    self.kv = KVStore(path)
    self.tables: Dict[str, TableDef] = {}

  def _get_table_def(self, name: str) -> Optional[TableDef]:
    if name in self.tables:
      return self.tables[name]
    rec = Record().add_str("name", name)
    found = self._get(TDEF_TABLE, rec)
    if not found:
      return None
    return TableDef.from_dict(json.loads(rec.get("def").string))

  def _escape_string(self, s: bytes) -> bytes:
    return s.replace(b"\1", b"\1\2").replace(b"\0", b"\1\1")

  def _encode_key(self, prefix: int, values: List[Value]) -> bytes:
    return binary.bytes4(prefix) + self._encode_values(values)

  def _encode_values(self, values: List[Value]) -> bytes:
    result = b''
    for val in values:
      match val.type:
        case ColumnType.BYTES:
          result += self._escape_string(val.bytes_) + b"\0"
        case ColumnType.INT:
          result += binary.bytes8(val.integer)
        case _:
          raise ValueError('Invalid column type')
    return result

  def _decode_values(self, data: bytes, types: List[ColumnType]) -> List[Value]:
    values: List[Value] = []
    for t in types:
      match t:
        case ColumnType.BYTES:
          i = data.find(b"\0")
          values.append(Value(
              t, data[:i].replace(b"\1\1", b"\0").replace(b"\1\2", b"\1"), 0
          ))
          data = data[i + 1:]
        case ColumnType.INT:
          values.append(Value(t, b'', binary.uint64(data)))
          data = data[8:]
        case _:
          raise ValueError('Invalid column type')
    return values

  # reorder a record and check for missing columns.
  # n == tdef.PKeys: record is exactly a primary key
  # n == len(tdef.Cols): record contains all columns
  def _check_record(self, tdef: TableDef, rec: Record, n: int) -> List[Value]:
    if len(rec.columns) != n:
      raise ValueError(
          f"Invalid number of columns. Expect {n}, found {len(tdef.columns)}"
      )
    values = []
    for i in range(n):
      found = False
      for column, value in zip(rec.columns, rec.values):
        if tdef.columns[i].name == column.name:
          values.append(value)
          found = True
          break
      if not found:
        raise KeyError(f"Column {tdef.columns[i].name} not found")
    return values

  def _get(self, tdef: TableDef, rec: Record) -> bool:
    values = self._check_record(tdef, rec, tdef.pkeys)
    key = self._encode_key(tdef.prefix, values)
    try:
      value = self.kv.get(key)
    except KeyError:
      return False
    rec.columns.extend(tdef.columns[tdef.pkeys:])
    rec.values.extend(
        self._decode_values(value, [x.type for x in tdef.columns[tdef.pkeys:]])
    )
    return True

  def _update(self, tdef: TableDef, rec: Record, mode: UpdateMode):
    values = self._check_record(tdef, rec, len(tdef.columns))
    key = self._encode_key(tdef.prefix, values[:tdef.pkeys])
    value = self._encode_values(values[tdef.pkeys:])
    self.kv.set(key, value)

  def _delete(self, tdef: TableDef, rec: Record):
    values = self._check_record(tdef, rec, tdef.pkeys)
    key = self._encode_key(tdef.prefix, values[:tdef.pkeys])
    self.kv.delete(key)

  def _set(self, table: str, rec: Record, mode: UpdateMode):
    tdef = self._get_table_def(table)
    if tdef is None:
      raise KeyError("Table not found")
    self._update(tdef, rec, mode)

  def get(self, table: str, rec: Record):
    tdef = self._get_table_def(table)
    if tdef is None:
      raise KeyError("Table not found")
    self._get(tdef, rec)

  def insert(self, table: str, rec: Record):
    self._set(table, rec, UpdateMode.INSERT_ONLY)

  def update(self, table: str, rec: Record):
    self._set(table, rec, UpdateMode.UPDATE_ONLY)

  def upsert(self, table: str, rec: Record):
    self._set(table, rec, UpdateMode.UPSERT)

  def delete(self, table: str, rec: Record):
    tdef = self._get_table_def(table)
    if tdef is None:
      raise KeyError("Table not found")
    self._delete(tdef, rec)

  def table_new(self, tdef: TableDef):
    table = Record().add_str("name", tdef.name)
    found = self._get(TDEF_TABLE, table)
    if found:
      raise KeyError("Table existed")
    assert tdef.prefix == 0
    tdef.prefix = 3
    meta = Record().add_str("key", "next_prefix")
    found = self._get(TDEF_META, meta)
    if found:
      tdef.prefix = binary.uint32(meta.get("value").bytes_)
    else:
      meta.add_bytes("value", binary.bytes4(0))
    meta.set_value("value", Value(ColumnType.BYTES,
                   binary.bytes4(tdef.prefix + 1), 0))
    self._update(TDEF_META, meta, UpdateMode.UPSERT)
    table.add_str("def", json.dumps(tdef.to_dict()))
    self._update(TDEF_TABLE, table, UpdateMode.UPSERT)

  def open(self):
    self.kv.open()

  def close(self):
    self.kv.close()
