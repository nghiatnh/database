from typing import List, Tuple
from dataclasses import dataclass

from database.constants import NodeType
from database.constants import PAGE_SIZE
from database.utils import binary


@dataclass
class NodeData:
  key: bytes
  value: bytes
  child: int = 0


class BNode:
  # BNode structure:
  # |--------------------------------------|
  # | type | nkeys | children... | data... |
  # | 2b   | 2b    | 8b * nkeys  | ...     |
  # |--------------------------------------|
  #
  # Data structure:
  # |-----------------------------------------------------------------|
  # | key length | value length | key             | value             |
  # | 2b         | 2b           | 1b * key length | 1b * value length |
  # |-----------------------------------------------------------------|

  def __init__(self, ntype: NodeType) -> None:
    self._type = ntype
    self._data: List[NodeData] = []

  def __repr__(self) -> str:
    kv_str = "Key-Value:\n    "
    kv_str += "\n    ".join(f"{x.key}: {x.value} " for x in self._data)
    child_str = "Children: " + ", ".join(str(x.child) for x in self._data)
    return f"BNode: {self.type.name}\n  " + child_str + "\n  " + kv_str

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def type(self) -> NodeType:
    return self._type

  @property
  def nkeys(self) -> int:
    return len(self._data)

  @property
  def total_bytes(self) -> int:
    return 2 + 2 + 8 * self.nkeys + sum(
        2 + 2 + len(x.key) + len(x.value) for x in self._data
    )

  def serialize(self) -> bytes:
    data = binary.bytes2(self.type.value) + binary.bytes2(self.nkeys)
    for i in range(self.nkeys):
      data += binary.bytes8(self.get_child(i))
    for i in range(self.nkeys):
      data_i = self.get(i)
      data += binary.bytes2(len(data_i.key)) + binary.bytes2(len(data_i.value))
      data += data_i.key + data_i.value
    return data

  @staticmethod
  def deserialize(data: bytes) -> "BNode":
    node = BNode(NodeType(binary.uint16(data[:2])))
    assert node.type in [NodeType.LEAF, NodeType.INTERNAL]
    nkeys = binary.uint16(data[2:4])
    child_data = data[4:4 + 8 * nkeys]
    data = data[4 + 8 * nkeys:]
    for i in range(nkeys):
      klen = binary.uint16(data[:2])
      vlen = binary.uint16(data[2:4])
      node.insert_data(i, data[4:4+klen], data[4+klen:4+klen+vlen])
      data = data[4+klen+vlen:]
    for i in range(nkeys):
      node.set_child(i, binary.uint64(child_data[:8]))
      child_data = child_data[8:]
    return node

  def insert_data(self, index: int, key: bytes, value: bytes):
    assert 0 <= index <= self.nkeys
    self._data.insert(index, NodeData(key, value))

  def set_child(self, index: int, child: int):
    self._data[index].child = child

  def get(self, index: int) -> NodeData:
    return self._data[index]

  def get_child(self, index: int) -> int:
    return self._data[index].child

  def lookup_le(self, key: bytes) -> int:
    found = 0
    for i in range(1, self.nkeys):
      if self.get(i).key > key:
        break
      found = i
    return found

  def leaf_insert(self, index: int, key: bytes, value: bytes) -> "BNode":
    assert self.type == NodeType.LEAF
    new = BNode(NodeType.LEAF)
    for i in range(index):
      new.insert_data(i, self.get(i).key, self.get(i).value)
      new.set_child(i, self.get_child(i))
    new.insert_data(index, key, value)
    for i in range(index, self.nkeys):
      new.insert_data(i + 1, self.get(i).key, self.get(i).value)
      new.set_child(i + 1, self.get_child(i))
    return new

  def leaf_update(self, index: int, key: bytes, value: bytes) -> "BNode":
    assert self.type == NodeType.LEAF
    new = BNode(NodeType.LEAF)
    for i in range(index):
      new.insert_data(i, self.get(i).key, self.get(i).value)
      new.set_child(i, self.get_child(i))
    new.insert_data(index, key, value)
    new.set_child(index, self.get_child(index))
    for i in range(index + 1, self.nkeys):
      new.insert_data(i, self.get(i).key, self.get(i).value)
      new.set_child(i, self.get_child(i))
    return new

  def leaf_delete(self, index: int) -> "BNode":
    new = BNode(self.type)
    for i in range(index):
      new.insert_data(i, self.get(i).key, self.get(i).value)
      new.set_child(i, self.get_child(i))
    for i in range(index + 1, self.nkeys):
      new.insert_data(i - 1, self.get(i).key, self.get(i).value)
      new.set_child(i - 1, self.get_child(i))
    return new

  def split2(self) -> Tuple["BNode", "BNode"]:
    lkeys = (self.nkeys + 1) // 2
    rkeys = self.nkeys - lkeys
    left = BNode(self.type)
    right = BNode(self.type)
    for i in range(lkeys):
      left.insert_data(i, self.get(i).key, self.get(i).value)
      left.set_child(i, self.get_child(i))
    for i in range(rkeys):
      right.insert_data(i, self.get(lkeys + i).key, self.get(lkeys + i).value)
      right.set_child(i, self.get_child(lkeys + i))
    assert right.total_bytes <= PAGE_SIZE
    return left, right

  def split3(self) -> List["BNode"]:
    if self.total_bytes <= PAGE_SIZE:
      return [self]
    left, right = self.split2()
    if left.total_bytes <= PAGE_SIZE:
      return [left, right]
    left, mid = left.split2()
    assert left.total_bytes <= PAGE_SIZE
    return [left, mid, right]

  def merge(self, right: "BNode") -> "BNode":
    new = BNode(self.type)
    for i in range(self.nkeys):
      new.insert_data(i, self.get(i).key, self.get(i).value)
      new.set_child(i, self.get_child(i))
    for i in range(right.nkeys):
      new.insert_data(i + self.nkeys, right.get(i).key, right.get(i).value)
      new.set_child(i + self.nkeys, right.get_child(i))
    return new

  def replace2kid(self, index: int, child: int, key: bytes) -> "BNode":
    new = BNode(self.type)
    for i in range(index):
      new.insert_data(i, self.get(i).key, self.get(i).value)
      new.set_child(i, self.get_child(i))
    new.insert_data(index, key, b"")
    new.set_child(index, child)
    for i in range(index + 2, self.nkeys):
      new.insert_data(i - 1, self.get(i).key, self.get(i).value)
      new.set_child(i - 1, self.get_child(i))
    return new
