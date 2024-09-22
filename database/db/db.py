from typing import Generator
from pathlib import Path
from enum import Enum
import json

from database.btree import SetRequest
from database.btree import DeleteRequest
from database.btree import BIter
from database.kvstore import KVStore
from database.kvstore import KVTX
from database.db import str_utils
from database.db.value import Value
from database.db.table import Record
from database.db.table import TableDef
from database.db.table import TDEF_META
from database.db.table import TDEF_TABLES
from database.db.scanner import Scanner
from database.constants import ValueType
from database.constants import SetMode
from database.constants import CompareOP
from database.constants import TDEF_MIN_PREFIX


class IndexOp(Enum):
  """
  IndexOp
  =======
  IndexOp class represents the index operation.
  """

  SET = 1
  DELETE = 2


class Database:
  """
  Database
  ========
  Database class represents the database manager.
  """

  def __init__(self, path: Path) -> None:
    self.kv = KVStore(path)

  def open(self) -> None:
    """
    Open the database.
    """
    self.kv.open()

  def close(self) -> None:
    """
    Close the database.
    """
    self.kv.close()

  def begin_read(self, tx: "DBTX") -> None:
    """
    Begin a read-only transaction.
    """
    self.kv.begin_read(tx.kv)

  def end_read(self, tx: "DBTX") -> None:
    """
    End a read-only transaction.
    """
    self.kv.end_read(tx.kv)

  def begin(self, tx: "DBTX"):
    """
    Begin a read-write transaction.
    """
    self.kv.begin(tx.kv)

  def commit(self, tx: "DBTX"):
    """
    Commit a read-write transaction.
    """
    self.kv.commit(tx.kv)

  def rollback(self, tx: "DBTX"):
    """
    Rollback a read-write transaction.
    """
    self.kv.rollback(tx.kv)


class DBTX:
  """
  DBTX
  ====
  DBTX class represents a database transaction.
  """

  def __init__(self) -> None:
    self.kv = KVTX()

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  def _scan(
      self,
      tdef: TableDef,
      key1: Value,
      key2: Value,
      cmp1: CompareOP,
      cmp2: CompareOP,
  ) -> Scanner:
    if cmp1.value * cmp2.value > 0:
      raise ValueError("Invalid scan range")
    if key1.name != key2.name:
      raise ValueError("Key names must match")
    if key1.type != key2.type:
      raise ValueError("Key types must match")
    index = tdef.find_index(key1.name)
    if key1.type != tdef.get_column_type(index.column):
      raise ValueError("Invalid key type")
    key_bytes1 = str_utils.encode_keys(index.prefix, [key1])
    key_bytes2 = str_utils.encode_keys(index.prefix, [key2])
    primary_type = tdef.get_column_type(tdef.primary_index.column)
    if key1.name != tdef.primary_index.column:
      if cmp1 in [CompareOP.LE, CompareOP.GT]:
        added = b"\xff" * 8 if primary_type == ValueType.INTEGER else b"\xff"
        key_bytes1 += added
      if cmp2 in [CompareOP.LE, CompareOP.GT]:
        added = b"\xff" * 8 if primary_type == ValueType.INTEGER else b"\xff"
        key_bytes2 += added
    sc = Scanner(key_bytes1, key_bytes2, cmp1, cmp2)
    sc.it = BIter.seek(self.kv.tree, sc.key1, sc.cmp1)
    return sc

  def _get(self, tdef: TableDef, key: Value) -> Record:
    if key.name != tdef.primary_index.column:
      raise ValueError(f"Key must be {tdef.primary_index.column}")
    sc = self._scan(tdef, key, key, CompareOP.GE, CompareOP.LE)
    if not sc.is_valid:
      return None
    columns = [tdef.primary_index.column]
    columns += [x for x in tdef.columns if x != tdef.primary_index.column]
    column_types = [tdef.get_column_type(tdef.primary_index.column)]
    column_types += [
        tp for x, tp in zip(tdef.columns, tdef.column_types)
        if x != tdef.primary_index.column
    ]
    return sc.deref(columns, column_types, 1, Record([]))

  def _set(self, tdef: TableDef, record: Record, mode: SetMode) -> bool:
    record = tdef.validate_record(record)
    keys = [record[tdef.primary_index.column]]
    values = [x for x in record.values if x.name != tdef.primary_index.column]
    key_bytes = str_utils.encode_keys(tdef.primary_index.prefix, keys)
    value_bytes = str_utils.encode_values(values)
    res = self.kv.set(SetRequest(key_bytes, value_bytes, mode))
    if not res.updated:
      raise ValueError(res.message)
    if not res.added:
      rec = Record([])
      for column, column_type in zip(tdef.columns, tdef.column_types):
        if column == tdef.primary_index.column:
          continue
        if column_type == ValueType.TEXT:
          rec.add_text(column, "")
        else:
          rec.add_integer(column, 0)
      rec = Record(str_utils.decode_values(res.old_value, rec.values))
      rec.values.append(record[tdef.primary_index.column])
      self._index_op(IndexOp.DELETE, tdef, rec)
    self._index_op(IndexOp.SET, tdef, record)
    return res.added

  def _delete(self, tdef: TableDef, key: Value) -> bool:
    if key.name != tdef.primary_index.column:
      raise ValueError(f"Key must be {tdef.primary_index.column}")
    key_bytes = str_utils.encode_keys(tdef.primary_index.prefix, [key])
    rec = self._get(tdef, key)
    if rec is None:
      return False
    res = self.kv.delete(DeleteRequest(key_bytes))
    if not res.deleted:
      raise ValueError(res.message)
    self._index_op(IndexOp.DELETE, tdef, rec)
    return True

  def _index_op(self, op: IndexOp, tdef: TableDef, record: Record) -> None:
    if op == IndexOp.SET:
      for index in tdef.indexes:
        keys = [record[index.column], record[tdef.primary_index.column]]
        key_bytes = str_utils.encode_keys(index.prefix, keys)
        self.kv.set(SetRequest(key_bytes, b"", SetMode.UPSERT))
    elif op == IndexOp.DELETE:
      for index in tdef.indexes:
        keys = [record[index.column], record[tdef.primary_index.column]]
        key_bytes = str_utils.encode_keys(index.prefix, keys)
        self.kv.delete(DeleteRequest(key_bytes))

  def _get_next_prefix(self) -> Record:
    rec = self._get(TDEF_META, Value.from_text("next_prefix", "key"))
    if rec is not None:
      return rec
    return Record([
        Value.from_text("next_prefix", "key"),
        Value.from_text(str(TDEF_MIN_PREFIX), "value"),
    ])

  def _update_next_prefix(self, prefix: int) -> None:
    rec = Record([
        Value.from_text("next_prefix", "key"),
        Value.from_text(str(prefix), "value"),
    ])
    self._set(TDEF_META, rec, SetMode.UPSERT)

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def get_table_def(self, table_name: str) -> TableDef:
    """
    Get the table definition by name.
    """
    rec = self._get(TDEF_TABLES, Value.from_text(table_name, "name"))
    if rec is None:
      return None
    return TableDef.from_dict(json.loads(rec["def"].text))

  def create_table(self, tdef: TableDef) -> None:
    """
    Create a table with the given table definition.
    """
    tdef.validate()
    if self.get_table_def(tdef.name) is not None:
      raise ValueError(f"Table {tdef.name} already exists")
    prefix = int(self._get_next_prefix()["value"].text)
    tdef.primary_index.prefix = prefix
    for index in tdef.indexes:
      prefix = prefix + 1
      index.prefix = prefix
    self._update_next_prefix(prefix + 1)
    self._set(
        TDEF_TABLES,
        Record([
            Value.from_text(tdef.name, "name"),
            Value.from_text(json.dumps(tdef.to_dict()), "def"),
        ]),
        SetMode.INSERT_ONLY,
    )

  def drop_table(self, table_name: str) -> None:
    """
    Drop the table by name.
    """
    tdef = self.get_table_def(table_name)
    if tdef is None:
      raise ValueError(f"Table {table_name} does not exist")
    self._delete(TDEF_TABLES, Value.from_text(table_name, "name"))

  def set(self, table_name: str, record: Record, mode: SetMode) -> bool:
    """
    Set the record in the table with the given mode.
    """
    tdef = self.get_table_def(table_name)
    if tdef is None:
      raise ValueError(f"Table {table_name} does not exist")
    return self._set(tdef, record, mode)

  def insert(self, table_name: str, record: Record) -> None:
    """
    Insert the record in the table.
    """
    self.set(table_name, record, SetMode.INSERT_ONLY)

  def update(self, table_name: str, record: Record) -> None:
    """
    Update the record in the table.
    """
    self.set(table_name, record, SetMode.UPDATE_ONLY)

  def delete(self, table_name: str, key: Value) -> None:
    """
    Delete the record from the table by key.
    """
    tdef = self.get_table_def(table_name)
    if tdef is None:
      raise ValueError(f"Table {table_name} does not exist")
    self._delete(tdef, key)

  def scan(
      self,
      table_name: str,
      key1: Value,
      key2: Value,
      cmp1: CompareOP,
      cmp2: CompareOP,
  ) -> Generator[Record, None, None]:
    """
    Scan the table with the given range and comparison operators. Return a
    generator of records.
    """
    tdef = self.get_table_def(table_name)
    if tdef is None:
      raise ValueError(f"Table {table_name} does not exist")
    sc = self._scan(tdef, key1, key2, cmp1, cmp2)
    while sc.is_valid:
      columns = [key1.name, tdef.primary_index.column]
      column_types = [
          tdef.get_column_type(key1.name),
          tdef.get_column_type(tdef.primary_index.column),
      ]
      rec = sc.deref(columns, column_types, 2, Record([]))
      yield self._get(tdef, rec[tdef.primary_index.column])
      sc.next()
