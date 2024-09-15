from typing import Optional
from dataclasses import dataclass

from database.btree import BIter
from database.db.record import Record
from database.db.table_def import TableDef
from database.db.str_utils import decode_values
from database.constants import CompareOP
from database.constants import COMPARE_FUNC


@dataclass
class Scanner:
  """
  Scanner
  =======
  Scanner class represents a scanner in the database. It contains the comparison
  operators, the keys, the index number, the end key, the table definition, and
  the iterator.
  """

  def __init__(
      self,
      cmp1: CompareOP,
      cmp2: CompareOP,
      key1: Record,
      key2: Record,
  ):
    self.cmp1 = cmp1
    self.cmp2 = cmp2
    self.key1 = key1
    self.key2 = key2
    self.index_no: int = -1
    self.key_end: bytes = b""
    self.tdef: Optional[TableDef] = None
    self.it: Optional[BIter] = None

  def __repr__(self) -> str:
    return (
        f"Scanner({self.cmp1}, {self.cmp2}, {self.key1}, {self.key2}, "
        f"{self.index_no}, {self.key_end})"
    )

  def __str__(self) -> str:
    return self.__repr__()

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def valid(self) -> bool:
    """
    Returns True if the scanner is valid, False otherwise.
    """
    assert self.it is not None
    if not self.it.valid():
      return False
    key, _ = self.it.deref()
    return COMPARE_FUNC[self.cmp2](key, self.key_end)

  def next(self):
    """
    Moves the scanner to the next key.
    """
    assert self.it is not None
    assert self.valid()
    if self.cmp1 in [CompareOP.GE, CompareOP.GT]:
      self.it.next()
    else:
      self.it.prev()

  def deref(self, rec: Record) -> bool:
    """
    Returns the record at the current scanner position.
    """
    assert self.it is not None
    assert self.tdef is not None
    assert self.valid()
    key, value = self.it.deref()
    rec.columns = self.tdef.columns
    if self.index_no == -1:
      rec.values = decode_values(
          key[4:], self.tdef.column_types[:self.tdef.pkeys]
      ) + decode_values(
          value, self.tdef.column_types[self.tdef.pkeys:]
      )
      return False
    assert len(value) == 0
    index = self.tdef.indexes[self.index_no]
    index_columns = [self.tdef.columns[self.tdef.col_index(c)] for c in index]
    index_values = decode_values(key[4:], [x.type for x in index_columns])
    icol = Record(columns=index_columns, values=index_values)
    rec.columns = self.tdef.columns[:self.tdef.pkeys]
    rec.values = [icol[c] for c in rec.column_names]
    return True
