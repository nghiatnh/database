from typing import List, Union, Tuple, Dict, Optional
from dataclasses import dataclass

from database.ql.ast_node import ASTNode
from database.ql.constants import TokenType
from database.ql.constants import ASTNodeType
from database.ql.constants import IndexOp
from database.constants import ValueType


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
  op: IndexOp
  value: Union[str, int]


@dataclass
class ComparisonTree:
  op: TokenType
  children: List[Union[Comparison, "ComparisonTree"]]


@dataclass
class IRCreateTable(IRNode):
  table: str
  columns: List[str]
  column_types: List[ValueType]
  pkey: str
  indexes: List[str]


@dataclass
class IRDropTable(IRNode):
  table: str


@dataclass
class IRScan(IRNode):
  table: str
  key1: Optional[Comparison]
  key2: Optional[Comparison]
  filter: Optional[ComparisonTree]
  offset: int
  limit: int


@dataclass
class IRSelect(IRScan, IRNode):
  aliases: Dict[str, str]


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
  # Table                                                                     #
  # ------------------------------------------------------------------------- #

  def _create_table(self, node: ASTNode) -> IRCreateTable:
    table, declarations = node.children
    columns, indexes, pkey = self._declarations(declarations)
    return IRCreateTable(
        table.token.value,
        [x[0] for x in columns],
        [x[1] for x in columns],
        pkey,
        indexes,
    )

  def _drop_table(self, node: ASTNode) -> IRDropTable:
    return IRDropTable(node.children[0].token.value)

  def _type(self, node: ASTNode) -> ValueType:
    return ValueType(node.token.value)

  def _field_decls(self, node: ASTNode) -> List[Tuple[str, ValueType]]:
    fields = []
    for field in node.children:
      name, tp = field.children
      fields.append((name.token.value, self._type(tp)))
    return fields

  def _index_decls(self, node: ASTNode) -> List[List[str]]:
    indexes = []
    for index in node.children:
      indexes.append(index.token.value)
    return indexes

  def _declarations(
      self, node: ASTNode
  ) -> Tuple[List[List[str]], int]:
    field_decls, index_decls, pkey_decls = node.children
    columns = self._field_decls(field_decls)
    indexes = self._index_decls(index_decls)
    pkey = pkey_decls.token.value
    return columns, indexes, pkey

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
    select_expr, table, conditions, offset, limit = node.children
    index, filt = self._conditions(conditions)
    return IRSelect(
        table=table.token.value,
        key1=index[0],
        key2=index[1],
        filter=filt,
        offset=self._offset(offset),
        limit=self._limit(limit),
        aliases=self._select_exprs(select_expr),
    )

  def _offset(self, node: ASTNode):
    return node.children[0].token.value if node.children else 0

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
    table, set_expr, conditions, offset, limit = node.children
    index, filt = self._visit(conditions)
    fields, values = self._set_exprs(set_expr)
    return IRUpdate(
        table=table.token.value,
        key1=index[0],
        key2=index[1],
        filter=filt,
        offset=self._offset(offset),
        limit=self._limit(limit),
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
    table, conditions, offset, limit = node.children
    index, filt = self._visit(conditions)
    return IRDelete(
        table=table.token.value,
        key1=index[0],
        key2=index[1],
        filter=filt,
        offset=self._offset(offset),
        limit=self._limit(limit),
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
          IndexOp(child.token.value),
          self._visit(value)
      )
    if len(node.children[1].children) == 0:
      return tuple(index), None
    filt = self._filter(node.children[1].children[0])
    return index, filt

  def _filter(self, node: ASTNode) -> ComparisonTree:
    if node.type == ASTNodeType.LOGIC:
      return ComparisonTree(
          node.token.type,
          [self._filter(x) for x in node.children]
      )
    field, value = node.children
    return Comparison(
        field.token.value,
        IndexOp(node.token.value),
        self._visit(value)
    )

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

  def _unary(self, node: ASTNode):
    if node.token.type == TokenType.MINUS:
      return -self._visit(node.children[0])
    return self._visit(node.children[0])

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def compile(self, root: ASTNode) -> List[IRNode]:
    """
    Compile the AST into intermediate representation nodes.
    """
    return self._statements(root)
