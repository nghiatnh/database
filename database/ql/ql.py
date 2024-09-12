from database.db import DatabaseTX
from database.db import Record
from database.db import Scanner
from database.db import Column
from database.constants import CompareOP
from database.ql.ir import IRDelete, IRCreateTable, IRInsert, IRUpdate, IRSelect


def _get_op(op: str):
  match op:
    case "<":
      return CompareOP.LT
    case "<=":
      return CompareOP.LE
    case ">":
      return CompareOP.GT
    case ">=":
      return CompareOP.GE


def execute(irs, db: DatabaseTX):
  db.begin()
  try:
    for ir in irs:
      if isinstance(ir, IRCreateTable):
        db.table_new(ir.table_def)
      elif isinstance(ir, IRInsert):
        rec = Record()
        for field, value in zip(ir.fields, ir.values):
          if isinstance(value, str):
            rec.add_string(field, value)
          else:
            rec.add_int(field, value)
        db.insert(ir.table, rec)
      elif isinstance(ir, IRUpdate):
        pass
      elif isinstance(ir, IRDelete):
        pass
      elif isinstance(ir, IRSelect):
        cmp1 = CompareOP.GE
        cmp2 = CompareOP.GT
        key1 = ''
        key2 = ''
        if ir.key1 is not None:
          cmp1 = _get_op(ir.key1.op)
          key1 = Record()
          if isinstance(ir.key1.value, str):
            key1.add_string(ir.key1.field, ir.key1.value)
          else:
            key1.add_int(ir.key1.field, ir.key1.value)
        if ir.key2 is not None:
          cmp2 = _get_op(ir.key2.op)
          key2 = Record()
          if isinstance(ir.key2.value, str):
            key2.add_string(ir.key2.field, ir.key2.value)
          else:
            key2.add_int(ir.key2.field, ir.key2.value)
        sc = Scanner(
            cmp1,
            cmp2,
            key1,
            key2,
        )
        it = db.scan(ir.table, sc)
        res = []
        while ir.limit < 0 or len(res) < ir.limit:
          try:
            rec = next(it)
            if ir.filter:
              match _get_op(ir.filter.op):
                case CompareOP.GE:
                  if not rec.values[rec.column_names.index(ir.filter.field)].value >= ir.filter.value:
                    continue
                case CompareOP.GT:
                  if not rec.values[rec.column_names.index(ir.filter.field)].value > ir.filter.value:
                    continue
                case CompareOP.LE:
                  if not rec.values[rec.column_names.index(ir.filter.field)].value <= ir.filter.value:
                    continue
                case CompareOP.LT:
                  if not rec.values[rec.column_names.index(ir.filter.field)].value < ir.filter.value:
                    continue
            res.append(rec)
          except StopIteration:
            break
        field2name = dict(zip(ir.fields, ir.names))

        for rec in res:
          rec.values = [
              x for col, x in zip(rec.column_names, rec.values)
              if col in field2name]
          rec.columns = [Column(field2name[x.name], x.type)
                         for x in rec.columns if x.name in field2name]
        print(res)
      else:
        raise ValueError("Invalid IR")
    db.commit()
  except Exception as e:
    db.abort()
    raise e
