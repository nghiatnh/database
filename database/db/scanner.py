from typing import List
from dataclasses import dataclass

from database.btree import BIter
from database.db import str_utils
from database.db.value import Value
from database.db.table import Record
from database.constants import CompareOP
from database.constants import ValueType
from database.constants import COMPARE_FN


@dataclass
class Scanner:
  """
  Scanner
  =======
  Scanner class represents a scanner for the database.
  """

  key1: bytes
  key2: bytes
  cmp1: CompareOP
  cmp2: CompareOP
  it: BIter = None

  @property
  def is_valid(self) -> bool:
    """
    Check if the scanner is valid to dereference.
    """
    if not self.it.is_valid:
      return False
    key, _ = self.it.deref()
    return (
        COMPARE_FN[self.cmp1](key, self.key1) and
        COMPARE_FN[self.cmp2](key, self.key2)
    )

  def deref(
      self,
      columns: List[str],
      column_types: List[ValueType],
      nkeys: int,
      rec: Record,
  ) -> Record:
    """
    Dereference the scanner to get the record.
    """
    key_bytes, value_bytes = self.it.deref()
    keys = str_utils.decode_values(
        key_bytes[8:],
        [
            Value.empty(tp, column)
            for tp, column in zip(column_types[:nkeys], columns[:nkeys])
        ],
    )
    values = str_utils.decode_values(
        value_bytes,
        [
            Value.empty(tp, column)
            for tp, column in zip(column_types[nkeys:], columns[nkeys:])
        ]
    )
    rec = Record(keys + values)
    return rec

  def next(self) -> None:
    """
    Move the scanner to the next record.
    """
    if self.cmp1 in [CompareOP.GE, CompareOP.GT]:
      self.it.move_next()
    else:
      self.it.move_prev()
