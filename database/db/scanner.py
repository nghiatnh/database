from dataclasses import dataclass

from database.btree import BIter
from database.db import str_utils
from database.db.value import Value
from database.db.table import Record
from database.db.table import TableDef
from database.constants import CompareOP
from database.constants import ValueType
from database.constants import COMPARE_FN


@dataclass
class Scanner:
  key1: bytes
  key2: bytes
  cmp1: CompareOP
  cmp2: CompareOP
  it: BIter = None

  @property
  def is_valid(self) -> bool:
    if not self.it.is_valid:
      return False
    key, _ = self.it.deref()
    return (
        COMPARE_FN[self.cmp1](key, self.key1) and
        COMPARE_FN[self.cmp2](key, self.key2)
    )

  def deref(self, tdef: TableDef, rec: Record) -> Record:
    key_bytes, value_bytes = self.it.deref()
    if tdef.get_column_type(tdef.primary_index.column) == ValueType.TEXT:
      key = str_utils.decode_values(
          key_bytes[8:], [Value.from_text("", tdef.primary_index.column)]
      )[0]
    else:
      key = str_utils.decode_values(
          key_bytes[8:], [Value.from_integer(0, tdef.primary_index.column)]
      )[0]
    values = []
    for column, tp in zip(tdef.columns, tdef.column_types):
      if column != key.name:
        if tp == ValueType.TEXT:
          values.append(Value.from_text("", column))
        else:
          values.append(Value.from_integer(0, column))
    str_utils.decode_values(value_bytes, values)
    rec = Record([key])
    rec.values.extend(values)
    return rec

  def next(self) -> None:
    if self.cmp1 in [CompareOP.GE, CompareOP.GT]:
      self.it.move_next()
    else:
      self.it.move_prev()
