from typing import List, Union
from dataclasses import dataclass

from database.db import DatabaseTX
from database.db import TableDef
from database.db import Column
from database.db import Record
from database.ql.ast_node import ASTNode
from database.constants import ColumnType
from database.constants import CompareOP


@dataclass
class IRCreateTable:
  table_def: TableDef


@dataclass
class Comparison:
  field: str
  op: CompareOP
  value: Union[str, int]


@dataclass
class IRScan:
  table: str
  key1: Comparison
  key2: Comparison
  filter: Comparison
  offset: int
  limit: int


@dataclass
class IRSelect(IRScan):
  fields: List[str]
  names: List[str]
  output: List[Record]


@dataclass
class IRUpdate(IRScan):
  fields: List[str]
  values: List[Union[str, int]]


@dataclass
class IRDelete(IRScan):
  pass


@dataclass
class IRInsert:
  table: str
  fields: List[str]
  values: List[Union[str, int]]


class IR:
  def __init__(self, db: DatabaseTX) -> None:
    self._db = db
    self._nodes = []

  def _visit(self, node: ASTNode):
    visit_fn = getattr(
        self, f"_{node.type.name.lower()}")
    return visit_fn(node)

  # ========================================================================= #
  # Analysis methods                                                          #
  # ========================================================================= #

  def _statements(self, node: ASTNode):
    for child in node.children:
      self._nodes.append(self._visit(child))

  def _create_table(self, node: ASTNode):
    table, declarations = node.children
    columns, indexes, pkeys = self._declarations(declarations)
    return IRCreateTable(
        table_def=TableDef(
            table.token.value,
            columns,
            pkeys,
            0,
            indexes,
            [],
        )
    )

  def _declarations(self, node: ASTNode):
    field_decls, index_decls, pkey_decls = node.children
    columns = []
    for field in field_decls.children:
      name, tp = field.children
      columns.append(Column(
          name.token.value,
          ColumnType.INT if tp.token.value == "INTEGER" else ColumnType.BYTES
      ))
    column_names = [x.name for x in columns]
    indexes = []
    for index in index_decls.children:
      ind = []
      for field in index.children:
        if field.token.value not in column_names:
          raise ValueError(f"index field not in fields: {field.token.value}")
        ind.append(field.token.value)
      indexes.append(ind)
    pkeys = []
    for pkey in pkey_decls.children:
      if pkey.token.value not in column_names:
        raise ValueError(f"primary key not in fields: {pkey.token.value}")
      pkeys.append(pkey.token.value)
    columns.sort(key=lambda x: x.name not in pkeys)
    return columns, indexes, len(pkeys)

  def _select(self, node: ASTNode):
    select_expr, table, conditions, limit = node.children
    index, filt = self._visit(conditions)
    return IRSelect(
        table=table.token.value,
        key1=index[0],
        key2=index[1],
        filter=filt,
        offset=0,
        limit=self._visit(limit),
        fields=[
            x.children[0].token.value for x in select_expr.children
        ],
        names=[
            x.children[1].token.value
            if len(x.children) > 1 else x.children[0].token.value
            for x in select_expr.children
        ],
        output=None,
    )

  def _insert(self, node: ASTNode):
    table, fields, values = node.children
    return IRInsert(
        table.token.value,
        [x.token.value for x in fields.children],
        [self._visit(x) for x in values.children]
    )

  def _update(self, node: ASTNode):
    table, set_expr, conditions, limit = node.children
    index, filt = self._visit(conditions)
    return IRUpdate(
        table.token.value,
        *index,
        filt,
        0,
        self._visit(limit),
        *self._visit(set_expr),
    )

  def _delete(self, node: ASTNode):
    table, conditions, limit = node.children
    index, filt = self._visit(conditions)
    return IRDelete(
        table.token.value,
        *index,
        filt,
        0,
        self._visit(limit),
    )

  def _number(self, node: ASTNode):
    return node.token.value

  def _string(self, node: ASTNode):
    return node.token.value

  def _limit(self, node: ASTNode):
    return node.children[0].token.value if node.children else -1

  def _set_exprs(self, node: ASTNode):
    names = [x.children[0].token.value for x in node.children]
    values = [self._visit(x.children[1]) for x in node.children]
    return names, values

  def _conditions(self, node: ASTNode):
    index = [None, None]
    for i, child in enumerate(node.children[0].children):
      field, value = child.children
      index[i] = Comparison(
          field.token.value,
          child.token.value,
          self._visit(value)
      )
    filt = None
    if node.children[1].children:
      field, value = node.children[1].children[0].children
      filt = Comparison(
          field.token.value,
          node.children[1].children[0].token.value,
          self._visit(value)
      )
    return index, filt

  def _arithmetic(self, node: ASTNode):
    if len(node.children) == 1:
      return self._arithmetic(node.children[0])
    left = self._visit(node.children[0])
    right = self._visit(node.children[1])
    fn = {
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "*": lambda x, y: x * y,
        "/": lambda x, y: x // y,
        "%": lambda x, y: x % y,
    }
    return fn[node.token.value](left, right)

  def compile(self, root: ASTNode):
    self._statements(root)
    return self._nodes
