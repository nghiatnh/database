from typing import List, Union, Tuple, Dict
from dataclasses import dataclass

from database.db import Column
from database.ql.ast_node import ASTNode
from database.constants import ColumnType
from database.constants import CompareOP


@dataclass
class IRNode:
  """
  IRNode
  ======
  IRNode class is the base class for all intermediate representation nodes.
  """


@dataclass
class Comparison:
  field: str
  op: CompareOP
  value: Union[str, int]


@dataclass
class IRCreateTable(IRNode):
  table: str
  columns: List[Column]
  pkeys: int
  indexes: List[List[str]]


@dataclass
class IRScan(IRNode):
  table: str
  key1: Comparison
  key2: Comparison
  filter: Comparison
  offset: int
  limit: int


@dataclass
class IRSelect(IRScan, IRNode):
  alias: Dict[str, str]


@dataclass
class IRUpdate(IRScan, IRNode):
  fields: List[str]
  values: List[Union[str, int]]


@dataclass
class IRDelete(IRScan, IRNode):
  pass


@dataclass
class IRInsert(IRNode):
  table: str
  fields: List[str]
  values: List[Union[str, int]]


class IR:
  """
  IR
  ==
  IR class represents the intermediate representation of the query language.
  """

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  def _visit(self, node: ASTNode):
    visit_fn = getattr(
        self, f"_{node.type.name.lower()}")
    return visit_fn(node)

  # ========================================================================= #
  # Analysis methods                                                          #
  # ========================================================================= #

  # ------------------------------------------------------------------------- #
  # Statements                                                                #
  # ------------------------------------------------------------------------- #

  def _statements(self, node: ASTNode) -> List[IRNode]:
    nodes = []
    for child in node.children:
      nodes.append(self._visit(child))
    return nodes

  # ------------------------------------------------------------------------- #
  # Create Table                                                              #
  # ------------------------------------------------------------------------- #

  def _create_table(self, node: ASTNode) -> IRCreateTable:
    table, declarations = node.children
    columns, indexes, pkeys = self._declarations(declarations)
    return IRCreateTable(
        table.token.value,
        columns,
        pkeys,
        indexes,
    )

  def _type(self, node: ASTNode) -> ColumnType:
    return ColumnType.INT if node.token.value == "INTEGER" else ColumnType.BYTES

  def _field_decls(self, node: ASTNode) -> List[Column]:
    fields = []
    for field in node.children:
      name, tp = field.children
      fields.append(Column(name.token.value, self._type(tp)))
    return fields

  def _index_decls(self, node: ASTNode) -> List[List[str]]:
    indexes = []
    for index in node.children:
      ind = []
      for field in index.children:
        ind.append(field.token.value)
      indexes.append(ind)
    return indexes

  def _primary_key_decls(self, node: ASTNode) -> List[str]:
    pkeys = []
    for pkey in node.children:
      pkeys.append(pkey.token.value)
    return pkeys

  def _declarations(
      self, node: ASTNode
  ) -> Tuple[List[Column], List[List[str]], int]:
    field_decls, index_decls, pkey_decls = node.children
    columns = self._field_decls(field_decls)
    indexes = self._index_decls(index_decls)
    pkeys = self._primary_key_decls(pkey_decls)
    columns.sort(key=lambda x: x.name not in pkeys)
    return columns, indexes, len(pkeys)

  # ------------------------------------------------------------------------- #
  # Select                                                                    #
  # ------------------------------------------------------------------------- #

  def _select_exprs(self, node: ASTNode) -> Dict[str, str]:
    aliases = {}
    for select_expr in node.children:
      field = select_expr.children[0].token.value
      if len(select_expr.children) == 1:
        aliases[field] = field
      else:
        aliases[field] = select_expr.children[1].token.value
    return aliases

  def _select(self, node: ASTNode) -> IRSelect:
    select_expr, table, conditions, limit = node.children
    index, filt = self._conditions(conditions)
    return IRSelect(
        table=table.token.value,
        key1=index[0],
        key2=index[1],
        filter=filt,
        offset=0,
        limit=self._limit(limit),
        alias=self._select_exprs(select_expr),
    )

  def _limit(self, node: ASTNode):
    return node.children[0].token.value if node.children else -1

  # ------------------------------------------------------------------------- #
  # Insert                                                                    #
  # ------------------------------------------------------------------------- #

  def _insert(self, node: ASTNode) -> IRInsert:
    table, fields, values = node.children
    return IRInsert(
        table.token.value,
        [x.token.value for x in fields.children],
        [self._visit(x) for x in values.children]
    )

  # ------------------------------------------------------------------------- #
  # Update                                                                    #
  # ------------------------------------------------------------------------- #

  def _update(self, node: ASTNode) -> IRUpdate:
    table, set_expr, conditions, limit = node.children
    index, filt = self._visit(conditions)
    fields, values = self._set_exprs(set_expr)
    return IRUpdate(
        table=table.token.value,
        key1=index[0],
        key2=index[1],
        filter=filt,
        offset=0,
        limit=self._visit(limit),
        fields=fields,
        values=values,
    )

  def _set_exprs(self, node: ASTNode):
    names = [x.children[0].token.value for x in node.children]
    values = [self._visit(x.children[1]) for x in node.children]
    return names, values

  # ------------------------------------------------------------------------- #
  # Delete                                                                    #
  # ------------------------------------------------------------------------- #

  def _delete(self, node: ASTNode) -> IRDelete:
    table, conditions, limit = node.children
    index, filt = self._visit(conditions)
    return IRDelete(
        table=table.token.value,
        key1=index[0],
        key2=index[1],
        filter=filt,
        offset=0,
        limit=self._visit(limit),
    )

  # ------------------------------------------------------------------------- #
  # Expressions                                                               #
  # ------------------------------------------------------------------------- #

  def _number(self, node: ASTNode) -> int:
    return node.token.value

  def _string(self, node: ASTNode) -> str:
    return node.token.value

  def _conditions(
      self, node: ASTNode
  ) -> Tuple[Tuple[Comparison, Comparison], Comparison]:
    index = [None, None]
    for i, child in enumerate(node.children[0].children):
      field, value = child.children
      index[i] = Comparison(
          field.token.value,
          CompareOP(child.token.value),
          self._visit(value)
      )
    filt = None
    if node.children[1].children:
      field, value = node.children[1].children[0].children
      filt = Comparison(
          field.token.value,
          CompareOP(node.children[1].children[0].token.value),
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

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def compile(self, root: ASTNode) -> List[IRNode]:
    """
    Compile the AST into intermediate representation nodes.
    """
    return self._statements(root)
