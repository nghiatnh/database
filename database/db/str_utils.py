from typing import List

from database.db.value import Value
from database.db.table_def import TableDef
from database.utils import binary
from database.constants import ColumnType
from database.constants import CompareOP


def _escape_string(s: bytes) -> bytes:
  s = s.replace(b"\1", b"\1\2").replace(b"\0", b"\1\1")
  if s[0] >= 254:
    s = b"\xfe" + s
  return s


def encode_values(values: List[Value]) -> bytes:
  result = b""
  for val in values:
    match val.type:
      case ColumnType.BYTES:
        result += _escape_string(val.bytes_) + b"\0"
      case ColumnType.INT:
        result += binary.bytes8(val.integer)
      case _:
        raise ValueError("Invalid column type")
  return result


def decode_values(data: bytes, types: List[ColumnType]) -> List[Value]:
  values: List[Value] = []
  for t in types:
    match t:
      case ColumnType.BYTES:
        i = data.find(b"\0")
        values.append(Value(
            t, data[:i].replace(b"\1\1", b"\0").replace(b"\1\2", b"\1"), 0
        ))
        data = data[i + 1:]
      case ColumnType.INT:
        values.append(Value(t, b"", binary.uint64(data)))
        data = data[8:]
      case _:
        raise ValueError("Invalid column type")
  return values


def encode_key(prefix: int, values: List[Value]) -> bytes:
  return binary.bytes4(prefix) + encode_values(values)


def encode_key_partial(
    prefix: int,
    values: List[Value],
    tdef: TableDef,
    keys: List[str],
    cmp: CompareOP,
):
  out = encode_key(prefix, values)
  if cmp in [CompareOP.GT, CompareOP.LE]:
    for i in range(len(values), len(keys)):
      match tdef.columns[tdef.col_index(keys[i])].type:
        case ColumnType.BYTES:
          out += b"\xff"
        case ColumnType.INT:
          out += b"\xff" * 8
          break
        case _:
          raise ValueError("Invalid column type")
  return out
