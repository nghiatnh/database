from typing import Union, List, Optional, Tuple

from database.db import DatabaseTX
from database.db import TableDef
from database.db import Record
from database.db import Value
from database.db import Scanner
from database.ql.lexer import Lexer
from database.ql.parser import Parser
from database.ql.ir import IR
from database.ql.ir import IRNode
from database.ql.ir import IRCreateTable
from database.ql.ir import IRScan
from database.ql.ir import IRSelect
from database.ql.ir import IRInsert
from database.ql.ir import IRUpdate
from database.ql.ir import IRDelete
from database.constants import CompareOP
from database.constants import ColumnType


class QLExecutor:
  """
  QLExecutor
  ==========
  QLExecutor class represents a query language that is used to interact with
  the database.
  """

  def __init__(self, db: DatabaseTX) -> None:
    self._db = db

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  def _execute(self, ir_node: IRNode) -> Optional[List[Record]]:
    if isinstance(ir_node, IRCreateTable):
      return self._ir_create_table(ir_node)
    if isinstance(ir_node, IRSelect):
      return self._execute_select(ir_node)
    if isinstance(ir_node, IRInsert):
      return self._execute_insert(ir_node)
    if isinstance(ir_node, IRUpdate):
      return self._execute_update(ir_node)
    if isinstance(ir_node, IRDelete):
      return self._execute_delete(ir_node)
    raise ValueError(f"Invalid IR node: {ir_node}")

  def _ir_create_table(self, ir_node: IRCreateTable):
    self._db.table_new(
        TableDef(
            name=ir_node.table,
            columns=ir_node.columns,
            pkeys=ir_node.pkeys,
            prefix=0,
            indexes=ir_node.indexes,
            index_prefixes=[],
        )
    )

  def _execute_scan(self, ir_node: IRScan) -> Tuple[List[Record], Scanner]:
    sc = Scanner(
        cmp1=ir_node.key1.op,
        cmp2=ir_node.key2.op,
        key1=self._value_to_record([ir_node.key1.field], [ir_node.key1.value]),
        key2=self._value_to_record([ir_node.key2.field], [ir_node.key2.value]),
    )
    it = self._db.scan(ir_node.table, sc)
    recs: List[Record] = []
    while ir_node.limit < 0 or len(recs) < ir_node.limit:
      try:
        rec = next(it)
        if ir_node.filter is not None:
          if ir_node.filter.op == CompareOP.GT:
            if rec[ir_node.filter.field].value <= ir_node.filter.value:
              continue
          elif ir_node.filter.op == CompareOP.GE:
            if rec[ir_node.filter.field].value < ir_node.filter.value:
              continue
          elif ir_node.filter.op == CompareOP.LT:
            if rec[ir_node.filter.field].value >= ir_node.filter.value:
              continue
          elif ir_node.filter.op == CompareOP.LE:
            if rec[ir_node.filter.field].value > ir_node.filter.value:
              continue
        recs.append(rec)
      except StopIteration:
        break
    return recs, sc

  def _execute_select(self, ir_node: IRSelect):
    recs, _ = self._execute_scan(ir_node)
    for rec in recs:
      rec.rename(ir_node.alias)
    return recs

  def _execute_insert(self, ir_node: IRInsert):
    rec = self._value_to_record(ir_node.fields, ir_node.values)
    self._db.insert(ir_node.table, rec)
    return [rec]

  def _execute_update(self, ir_node: IRUpdate):
    recs, _ = self._execute_scan(ir_node)
    for rec in recs:
      for field, value in zip(ir_node.fields, ir_node.values):
        rec[field] = self._to_value(value)
    for rec in recs:
      self._db.update(ir_node.table, rec)
    return recs

  def _execute_delete(self, ir_node: IRDelete):
    recs, sc = self._execute_scan(ir_node)
    for rec in recs:
      rec = Record(
          columns=[
              x for x in rec.columns
              if x.name in sc.tdef.column_names[: sc.tdef.pkeys]
          ],
          values=[
              rec[x.name] for x in rec.columns
              if x.name in sc.tdef.column_names[: sc.tdef.pkeys]
          ],
      )
      self._db.delete(ir_node.table, rec)
    return recs

  def _to_value(self, value: Union[str, int]) -> Value:
    if isinstance(value, str):
      return Value(ColumnType.BYTES, value.encode("utf-8"), 0)
    return Value(ColumnType.INT, b"", value)

  def _value_to_record(
      self, fields: List[str],
      values: List[Union[str, int]],
  ) -> Record:
    rec = Record()
    for field, value in zip(fields, values):
      if isinstance(value, str):
        rec.add_string(field, value)
      else:
        rec.add_int(field, value)
    return rec

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def execute(self, query: str) -> Optional[List[Record]]:
    """
    Executes a query.
    """
    lexer = Lexer(query)
    parser = Parser(lexer)
    ast = parser.parse()
    ir_nodes = IR().compile(ast)
    self._db.begin()
    res = None
    try:
      for node in ir_nodes:
        res = self._execute(node)
      self._db.commit()
    except Exception as e:
      self._db.abort()
      raise e
    return res
