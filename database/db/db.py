from typing import Generator
from pathlib import Path
import json

from database.btree import BIter
from database.kvstore import KVStore
from database.db import str_utils
from database.db.value import Value
from database.db.table import Record
from database.db.table import TableDef
from database.db.table import TDEF_META
from database.db.table import TDEF_TABLES
from database.db.scanner import Scanner
from database.constants import CompareOP
from database.constants import TDEF_MIN_PREFIX


class Database:
  def __init__(self, path: Path) -> None:
    self.kv = KVStore(path)

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
    key_bytes1 = str_utils.encode_keys(tdef.primary_index.prefix, [key1])
    key_bytes2 = str_utils.encode_keys(tdef.primary_index.prefix, [key2])
    sc = Scanner(key_bytes1, key_bytes2, cmp1, cmp2)
    sc.it = BIter.seek(self.kv.tree, sc.key1, sc.cmp1)
    return sc

  def _get(self, tdef: TableDef, key: Value) -> Record:
    if key.name != tdef.primary_index.column:
      raise ValueError(f"Key must be {tdef.primary_index.column}")
    sc = self._scan(tdef, key, key, CompareOP.GE, CompareOP.LE)
    if not sc.is_valid:
      return None
    return sc.deref(tdef, Record([]))

  def _set(self, tdef: TableDef, record: Record) -> None:
    record = tdef.validate_record(record)
    keys = [record[tdef.primary_index.column]]
    values = [x for x in record.values if x.name != tdef.primary_index.column]
    key_bytes = str_utils.encode_keys(tdef.primary_index.prefix, keys)
    value_bytes = str_utils.encode_values(values)
    self.kv.insert(key_bytes, value_bytes)

  def _delete(self, tdef: TableDef, key: Value) -> None:
    if key.name != tdef.primary_index.column:
      raise ValueError(f"Key must be {tdef.primary_index.column}")
    key_bytes = str_utils.encode_keys(tdef.primary_index.prefix, [key])
    self.kv.delete(key_bytes)

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
    self._set(TDEF_META, rec)

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def open(self) -> None:
    self.kv.open()

  def close(self) -> None:
    self.kv.close()

  def get_table_def(self, table_name: str) -> TableDef:
    rec = self._get(TDEF_TABLES, Value.from_text(table_name, "name"))
    if rec is None:
      return None
    return TableDef.from_dict(json.loads(rec["def"].text))

  def create_table(self, tdef: TableDef) -> None:
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
    )

  def insert(self, table_name: str, record: Record) -> None:
    tdef = self.get_table_def(table_name)
    if tdef is None:
      raise ValueError(f"Table {table_name} does not exist")
    self._set(tdef, record)

  def delete(self, table_name: str, key: Value) -> None:
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
    tdef = self.get_table_def(table_name)
    if tdef is None:
      raise ValueError(f"Table {table_name} does not exist")
    sc = self._scan(tdef, key1, key2, cmp1, cmp2)
    while sc.is_valid:
      yield sc.deref(tdef, Record([]))
      sc.next()
