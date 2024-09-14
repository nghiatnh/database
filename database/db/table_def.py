from typing import List, Dict
from dataclasses import dataclass

from database.db.record import Column
from database.constants import ColumnType


@dataclass
class TableDef:
  """
  TableDef
  ========
  TableDef class represents a table definition in the database. It contains the
  name of the table, the columns, the primary key columns, the prefix, the
  indexes, and the index prefixes.
  """

  name: str
  columns: List[Column]
  pkeys: int
  prefix: int
  indexes: List[List[str]]
  index_prefixes: List[int]

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

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

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def n_cols(self) -> int:
    """
    Returns the number of columns in the table.
    """
    return len(self.columns)

  @property
  def column_names(self) -> List[str]:
    """
    Returns the names of the columns in the table.
    """
    return [x.name for x in self.columns]

  @property
  def column_types(self) -> List[ColumnType]:
    """
    Returns the types of the columns in the table.
    """
    return [x.type for x in self.columns]

  @staticmethod
  def from_dict(data: dict) -> "TableDef":
    """
    Creates a TableDef object from a dictionary.
    """
    return TableDef(
        data["name"],
        [Column(x["name"], ColumnType(x["type"])) for x in data["columns"]],
        data["pkeys"],
        data["prefix"],
        data["indexes"],
        data["index_prefixes"],
    )

  def to_dict(self) -> dict:
    """
    Converts the TableDef object into a dictionary.
    """
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
    """
    Checks the table definition for consistency.
    """
    for i, index in enumerate(self.indexes):
      self.indexes[i] = self._check_index_keys(index)

  def find_index(self, keys: List[str]) -> int:
    """
    Finds the index that matches the given keys.
    """
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
    """
    Returns the index of the column in the table.
    """
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
"""
This table stores the metadata. It has two columns: key and value.
"""

TDEF_TABLE = TableDef(
    name="@table",
    columns=[Column("name", ColumnType.BYTES), Column("def", ColumnType.BYTES)],
    pkeys=1,
    prefix=2,
    indexes=[],
    index_prefixes=[],
)
"""
This table stores the table definitions. It has two columns: name and def.
"""
