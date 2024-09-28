from typing import Union, List, Optional, Generator

from database.db import Index
from database.db import DBTX
from database.db import Database
from database.db import TableDef
from database.db import Table
from database.db import Record
from database.db import Value
from database.ql.lexer import Lexer
from database.ql.parser import Parser
from database.ql.ir import Comparison
from database.ql.ir import ComparisonTree
from database.ql.ir import IR
from database.ql.ir import IRNode
from database.ql.ir import IRCreateTable
from database.ql.ir import IRDropTable
from database.ql.ir import IRScan
from database.ql.ir import IRSelect
from database.ql.ir import IRInsert
from database.ql.ir import IRUpdate
from database.ql.ir import IRDelete
from database.ql.constants import TokenType
from database.ql.constants import IndexOp
from database.constants import CompareOP
from database.constants import ValueType
from database.utils import binary


COMPARE_FN = {
    TokenType.EQ.value: lambda x, y: x == y,
    TokenType.NEQ.value: lambda x, y: x != y,
    TokenType.GT.value: lambda x, y: x > y,
    TokenType.GE.value: lambda x, y: x >= y,
    TokenType.LT.value: lambda x, y: x < y,
    TokenType.LE.value: lambda x, y: x <= y,
}

LOGIC_FN = {
    TokenType.AND.value: lambda x, y: x and y,
    TokenType.OR.value: lambda x, y: x or y,
}

INDEX_TO_COMPARE_OP = {
    IndexOp.LT: CompareOP.LT,
    IndexOp.LE: CompareOP.LE,
    IndexOp.GT: CompareOP.GT,
    IndexOp.GE: CompareOP.GE,
}

OPPOSITE_OP = {
    IndexOp.LT: IndexOp.GE,
    IndexOp.LE: IndexOp.GE,
    IndexOp.GT: IndexOp.LE,
    IndexOp.GE: IndexOp.LE,
}


class QLExecutor:
  """
  QLExecutor
  ==========
  QLExecutor class represents a query language that is used to interact with
  the database.
  """

  def __init__(self, db: Database) -> None:
    self._db = db

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  def _execute(self, ir_node: IRNode, tx: DBTX) -> Optional[Table]:
    if isinstance(ir_node, IRCreateTable):
      return self._execute_create_table(ir_node, tx)
    if isinstance(ir_node, IRDropTable):
      return self._execute_drop_table(ir_node, tx)
    if isinstance(ir_node, IRSelect):
      return self._execute_select(ir_node, tx)
    if isinstance(ir_node, IRInsert):
      return self._execute_insert(ir_node, tx)
    if isinstance(ir_node, IRUpdate):
      return self._execute_update(ir_node, tx)
    if isinstance(ir_node, IRDelete):
      return self._execute_delete(ir_node, tx)
    raise ValueError(f"Invalid IR node: {ir_node}")

  def _execute_create_table(self, ir_node: IRCreateTable, tx: DBTX):
    tx.create_table(
        TableDef(
            name=ir_node.table,
            columns=ir_node.columns,
            column_types=ir_node.column_types,
            primary_index=Index(ir_node.pkey),
            indexes=[Index(x) for x in ir_node.indexes],
        )
    )

  def _execute_drop_table(self, ir_node: IRDropTable, tx: DBTX):
    self._execute_delete(
        IRDelete(
            table=ir_node.table,
            key1=None,
            key2=None,
            filter=None,
            offset=0,
            limit=-1,
        ),
        tx,
    )
    tx.drop_table(ir_node.table)

  def _execute_scan(self, ir_node: IRScan, tx: DBTX) -> Table:
    it = self._get_scanner(ir_node.table, ir_node.key1, ir_node.key2, tx)
    table = Table([])
    offset = 0
    while ir_node.limit < 0 or table.n_records < ir_node.limit:
      try:
        rec = next(it)
        if not self._eval(ir_node.filter, rec):
          continue
        if offset < ir_node.offset:
          offset += 1
          continue
        table.records.append(rec)
      except StopIteration:
        break
    return table

  def _execute_select(self, ir_node: IRSelect, tx: DBTX) -> Table:
    table = self._execute_scan(ir_node, tx)
    for rec in table.records:
      rec.select(ir_node.aliases)
    return table

  def _execute_insert(self, ir_node: IRInsert, tx: DBTX) -> Table:
    rec = self._value_to_record(ir_node.fields, ir_node.values)
    tx.insert(ir_node.table, rec)
    return Table([rec])

  def _execute_update(self, ir_node: IRUpdate, tx: DBTX) -> Table:
    table = self._execute_scan(ir_node, tx)
    for rec in table.records:
      for field, value in zip(ir_node.fields, ir_node.values):
        rec[field] = self._to_value(value, field)
    for rec in table.records:
      tx.update(ir_node.table, rec)
    return table

  def _execute_delete(self, ir_node: IRDelete, tx: DBTX):
    table = self._execute_scan(ir_node, tx)
    tdef = tx.get_table_def(ir_node.table)
    for rec in table.records:
      tx.delete(ir_node.table, rec[tdef.primary_index.column])
    return table

  def _get_scanner(
      self,
      table: str,
      key1: Optional[Comparison],
      key2: Optional[Comparison],
      tx: DBTX,
  ) -> Generator[Record, None, None]:
    tdef = tx.get_table_def(table)
    if tdef is None:
      raise ValueError(f"Table {table} does not exist")
    if key1 is None:
      field = tdef.primary_index.column
      column_type = tdef.column_types[tdef.columns.index(field)]
      key1 = Comparison(
          field,
          IndexOp.GE,
          self._parital_value(IndexOp.LE, column_type),
      )
    if key1.op == IndexOp.EQ and key2 is not None:
      raise ValueError("Invalid query: EQ and key2 is not None")
    if key2 is None:
      if key1.op == IndexOp.EQ:
        key2 = Comparison(
            key1.field,
            IndexOp.LE,
            key1.value,
        )
        key1.op = IndexOp.GE
      else:
        column_type = tdef.column_types[tdef.columns.index(key1.field)]
        key2 = Comparison(
            key1.field,
            OPPOSITE_OP[key1.op],
            self._parital_value(key1.op, column_type),
        )
    return tx.scan(
        table,
        self._to_value(key1.value, key1.field),
        self._to_value(key2.value, key2.field),
        INDEX_TO_COMPARE_OP[key1.op],
        INDEX_TO_COMPARE_OP[key2.op],
    )

  def _parital_value(
      self,
      op: IndexOp,
      value_type: ValueType,
  ) -> Union[str, int]:
    if op == IndexOp.LE:
      return "" if value_type == ValueType.TEXT else 0
    return (
        b"\xff".decode() if value_type == ValueType.TEXT
        else binary.int64(b"\xff" * 8)
    )

  def _to_value(self, value: Union[str, int], name: str) -> Value:
    if isinstance(value, str):
      return Value.from_text(value, name)
    return Value.from_integer(value, name)

  def _value_to_record(
      self, fields: List[str],
      values: List[Union[str, int]],
  ) -> Record:
    rec = Record([])
    for field, value in zip(fields, values):
      if isinstance(value, str):
        rec.add_text(field, value)
      else:
        rec.add_integer(field, value)
    return rec

  def _eval(self, node: Union[Comparison, ComparisonTree], rec: Record) -> bool:
    if node is None:
      return True
    if node.op.value in LOGIC_FN:
      return LOGIC_FN[node.op](
          self._eval(node.children[0], rec),
          self._eval(node.children[1], rec)
      )
    return COMPARE_FN[node.op.value](rec[node.field].value, node.value)

  def _execute_read_only(self, nodes: List[IRNode]) -> Optional[Table]:
    res = []
    tx = DBTX()
    self._db.begin_read(tx)
    try:
      for node in nodes:
        res = self._execute(node, tx)
    finally:
      self._db.end_read(tx)
    return res

  def _execute_read_write(self, nodes: List[IRNode]) -> Optional[Table]:
    res = []
    tx = DBTX()
    self._db.begin(tx)
    try:
      for node in nodes:
        res = self._execute(node, tx)
      self._db.commit(tx)
    except Exception as e:
      self._db.rollback(tx)
      raise e
    return res

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def execute(self, query: str) -> Optional[Table]:
    """
    Executes a query. It begins a read transaction if the query is read-only
    and a read-write transaction otherwise.
    """
    lexer = Lexer(query)
    parser = Parser(lexer)
    ast = parser.parse()
    ir_nodes = IR().compile(ast)
    is_readonly = all(isinstance(x, IRSelect) for x in ir_nodes)
    if is_readonly:
      return self._execute_read_only(ir_nodes)
    return self._execute_read_write(ir_nodes)
