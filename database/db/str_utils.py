from typing import List

from database.db.value import Value
from database.utils import binary
from database.constants import ValueType


def _escape_text(text: bytes) -> bytes:
  return text.replace(b"\1", b"\1\2").replace(b"\0", b"\1\1")


def encode_values(values: List[Value]) -> bytes:
  """
  Encode the values to bytes.
  """
  res = b""
  for v in values:
    if v.type == ValueType.TEXT:
      res += _escape_text(v.data) + b"\0"
    else:
      res += v.data
  return res


def encode_keys(prefix: int, keys: List[Value]) -> bytes:
  """
  Encode the keys to bytes.
  """
  return binary.bytes8(prefix) + encode_values(keys)


def decode_values(data: bytes, out: List[Value]) -> List[Value]:
  """
  Decode the values from bytes.
  """
  for v in out:
    if v.type == ValueType.TEXT:
      end = data.find(b"\0")
      v.data = data[:end].replace(b"\1\1", b"\0").replace(b"\1\2", b"\1")
      data = data[end + 1:]
    else:
      v.data = data[:8]
      data = data[8:]
  return out
