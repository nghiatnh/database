from typing import List, Dict, Optional, Generator
import json

from database.btree import DeleteReq, InsertReq
from database.db.value import Value
from database.db.record import Record
from database.db.table_def import TableDef
from database.db.table_def import TDEF_META
from database.db.table_def import TDEF_TABLE
from database.db.scanner import Scanner
from database.db import str_utils
from database.utils import binary
from database.constants import CompareOP
from database.constants import IndexOP
from database.constants import UpdateMode
from database.constants import ColumnType
from database.kvstore import KVTX
from database.db.db import Database


class DatabaseTX:
  """
  DatabaseTX
  ==========
  DatabaseTX class represents a database transaction. It provides methods to
  get, insert, update, delete and scan records in the database.
  """

  def __init__(self, path: str):
    self.kv: KVTX = KVTX()
    self.db = Database(path)
    self.tables: Dict[str, TableDef] = {}

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

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
    sc = Scanner(CompareOP.GE, CompareOP.LE, rec, rec)
    self._scan(tdef, sc)
    if sc.valid():
      if sc.deref(rec):
        found = self._get(tdef, rec)
        assert found
      return True
    return False

  def _update(self, tdef: TableDef, rec: Record, mode: UpdateMode) -> bool:
    values = self._check_record(tdef, rec, len(tdef.columns))
    key = str_utils.encode_key(tdef.prefix, values[:tdef.pkeys])
    value = str_utils.encode_values(values[tdef.pkeys:])
    req = InsertReq(key=key, value=value, mode=mode)
    self.kv.update(req)
    if not req.updated or len(tdef.indexes) == 0:
      return False
    if req.updated and not req.added:
      values[tdef.pkeys:] = str_utils.decode_values(
          req.old, [x.type for x in tdef.columns[tdef.pkeys:]])
      tmp = Record()
      tmp.columns = tdef.columns
      tmp.values = values
      self._index_op(tdef, tmp, IndexOP.DELETE)
    if req.updated:
      self._index_op(tdef, rec, IndexOP.ADD)
    return req.updated

  def _delete(self, tdef: TableDef, rec: Record) -> bool:
    values = self._check_record(tdef, rec, tdef.pkeys)
    key = str_utils.encode_key(tdef.prefix, values[:tdef.pkeys])
    req = DeleteReq(key)
    success = self.kv.delete(req)
    if not req.deleted or len(tdef.indexes) == 0:
      return False
    if req.deleted:
      values[tdef.pkeys:] = str_utils.decode_values(
          req.old, [x.type for x in tdef.columns[tdef.pkeys:]])
      tmp = Record()
      tmp.columns = tdef.columns
      tmp.values = values
      self._index_op(tdef, tmp, IndexOP.DELETE)
    return success

  def _set(self, table: str, rec: Record, mode: UpdateMode) -> bool:
    tdef = self.get_table_def(table)
    if tdef is None:
      raise KeyError("Table not found")
    return self._update(tdef, rec, mode)

  def _scan(self, tdef: TableDef, sc: "Scanner"):
    assert (
        (sc.cmp1 in [CompareOP.GE, CompareOP.GT] and
         sc.cmp2 in [CompareOP.LE, CompareOP.LT]) or
        (sc.cmp1 in [CompareOP.LE, CompareOP.LT] and
         sc.cmp2 in [CompareOP.GE, CompareOP.GT])
    )
    # values1 = self._check_record(tdef, sc.key1, tdef.pkeys)
    # values2 = self._check_record(tdef, sc.key2, tdef.pkeys)
    index_no = tdef.find_index([x.name for x in sc.key1.columns])
    index, prefix = [x.name for x in tdef.columns[:tdef.pkeys]], tdef.prefix
    if index_no >= 0:
      index, prefix = tdef.indexes[index_no], tdef.index_prefixes[index_no]
    sc.tdef = tdef
    sc.index_no = index_no
    key_start = str_utils.encode_key_partial(
        prefix, sc.key1.values, tdef, index, sc.cmp1)
    sc.key_end = str_utils.encode_key_partial(
        prefix, sc.key2.values, tdef, index, sc.cmp2)
    sc.it = self.kv.seek(key_start, sc.cmp1)

  def _index_op(self, tdef: TableDef, rec: Record, op: IndexOP):
    for i, index in enumerate(tdef.indexes):
      key = str_utils.encode_key(
          tdef.index_prefixes[i], [rec[c] for c in index])
      match op:
        case IndexOP.ADD:
          self.kv.update(InsertReq(key, b"", UpdateMode.UPSERT))
        case IndexOP.DELETE:
          self.kv.delete(DeleteReq(key))

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def get_table_def(self, name: str) -> Optional[TableDef]:
    """
    Returns the table definition for the given table name. If the table is not
    found, it returns None.
    """
    if name in self.tables:
      return self.tables[name]
    rec = Record().add_string("name", name)
    found = self._get(TDEF_TABLE, rec)
    if not found:
      return None
    return TableDef.from_dict(json.loads(rec["def"].string))

  def get(self, table: str, rec: Record):
    """
    Returns the record for the given table and record.
    """
    tdef = self.get_table_def(table)
    if tdef is None:
      raise KeyError("Table not found")
    self._get(tdef, rec)

  def insert(self, table: str, rec: Record) -> bool:
    """
    Inserts a record into the given table.
    """
    return self._set(table, rec, UpdateMode.INSERT_ONLY)

  def update(self, table: str, rec: Record) -> bool:
    """
    Updates a record in the given table.
    """
    return self._set(table, rec, UpdateMode.UPDATE_ONLY)

  def upsert(self, table: str, rec: Record) -> bool:
    """
    Updates or inserts a record in the given table.
    """
    return self._set(table, rec, UpdateMode.UPSERT)

  def delete(self, table: str, rec: Record) -> bool:
    """
    Deletes a record from the given table.
    """
    tdef = self.get_table_def(table)
    if tdef is None:
      raise KeyError("Table not found")
    return self._delete(tdef, rec)

  def scan(self, table: str, sc: "Scanner") -> Generator[Record, None, None]:
    """
    Scans the records in the given table using the scanner. It returns a
    generator of records.
    """
    tdef = self.get_table_def(table)
    if tdef is None:
      raise KeyError("Table not found")
    self._scan(tdef, sc)
    while sc.valid():
      rec = Record()
      if sc.deref(rec):
        self._get(tdef, rec)
        yield rec
      sc.next()

  def table_new(self, tdef: TableDef):
    """
    Creates a new table in the database.
    """
    tdef.check()
    table = Record().add_string("name", tdef.name)
    found = self._get(TDEF_TABLE, table)
    if found:
      raise KeyError("Table existed")
    assert tdef.prefix == 0
    tdef.prefix = 3
    meta = Record().add_string("key", "next_prefix")
    found = self._get(TDEF_META, meta)
    if found:
      tdef.prefix = binary.uint32(meta["value"].bytes_)
    else:
      meta.add_bytes("value", binary.bytes4(0))
    for i in range(len(tdef.indexes)):
      prefix = tdef.prefix + 1 + i
      tdef.index_prefixes.append(prefix)
    ntree = 1 + len(tdef.indexes)
    meta["value"] = Value(
        ColumnType.BYTES, binary.bytes4(tdef.prefix + ntree), 0)
    self._update(TDEF_META, meta, UpdateMode.UPSERT)
    table.add_string("def", json.dumps(tdef.to_dict()))
    self._update(TDEF_TABLE, table, UpdateMode.UPSERT)

  def open(self):
    """
    Opens the database transaction.
    """
    self.db.open()

  def close(self):
    """
    Closes the database transaction
    """
    self.db.close()

  def begin(self) -> "DatabaseTX":
    """
    Begins a transaction.
    """
    self.db.begin(self)
    return self

  def commit(self):
    """
    Commits the transaction. It writes the changes made during the transaction
    to the file.
    """
    self.db.commit(self)

  def abort(self):
    """
    Aborts the transaction. It discards the changes made during the transaction.
    """
    self.db.abort(self)
