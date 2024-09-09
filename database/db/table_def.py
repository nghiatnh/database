from typing import List, Dict
from dataclasses import dataclass

from database.db.record import Column
from database.constants import ColumnType


@dataclass
class TableDef:
  name: str
  columns: List[Column]
  pkeys: int
  prefix: int
  indexes: List[List[str]]
  index_prefixes: List[int]

  def _check_index_keys(self, index: List[str]) -> List[str]:
    icols: Dict[str, bool] = {}
    for c in index:
      if c not in [x.name for x in self.columns]:
        raise KeyError(f"Invalid column {c}")
      icols[c] = True
    for c in self.columns[:self.pkeys]:
      if c.name not in icols or not icols[c.name]:
        index.append(c.name)
    assert len(index) < self.n_cols
    return index

  def _is_prefix(self, long: List[str], short: List[str]) -> bool:
    if len(long) < len(short):
      return False
    for i, s in enumerate(short):
      if long[i] != s:
        return False
    return True

  @property
  def n_cols(self) -> int:
    return len(self.columns)

  @property
  def column_names(self) -> List[str]:
    return [x.name for x in self.columns]

  @property
  def column_types(self) -> List[ColumnType]:
    return [x.type for x in self.columns]

  @staticmethod
  def from_dict(data: dict) -> "TableDef":
    return TableDef(
        data["name"],
        [Column(x["name"], ColumnType(x["type"])) for x in data["columns"]],
        data["pkeys"],
        data["prefix"],
        data["indexes"],
        data["index_prefixes"],
    )

  def to_dict(self) -> dict:
    return {
        "name": self.name,
        "columns": [
            {"name": x.name, "type": x.type.value, } for x in self.columns
        ],
        "pkeys": self.pkeys,
        "prefix": self.prefix,
        "indexes": self.indexes,
        "index_prefixes": self.index_prefixes,
    }

  def check(self):
    for i, index in enumerate(self.indexes):
      self.indexes[i] = self._check_index_keys(index)

  def find_index(self, keys: List[str]) -> int:
    if self._is_prefix(self.column_names[:self.pkeys], keys):
      return -1
    winner = -2
    for i, index in enumerate(self.indexes):
      if not self._is_prefix(index, keys):
        continue
      if winner == -2 or len(index) < len(self.indexes[winner]):
        winner = i
    if winner == -2:
      raise ValueError("No index found")
    return winner

  def col_index(self, col: str) -> int:
    if col in self.column_names:
      return self.column_names.index(col)
    return -1


# =========================================================================== #
# Constants                                                                   #
# =========================================================================== #

TDEF_META = TableDef(
    name="@meta",
    columns=[
        Column("key", ColumnType.BYTES), Column("value", ColumnType.BYTES)
    ],
    pkeys=1,
    prefix=1,
    indexes=[],
    index_prefixes=[],
)

TDEF_TABLE = TableDef(
    name="@table",
    columns=[Column("name", ColumnType.BYTES), Column("def", ColumnType.BYTES)],
    pkeys=1,
    prefix=2,
    indexes=[],
    index_prefixes=[],
)
