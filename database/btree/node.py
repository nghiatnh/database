from typing import List
from dataclasses import dataclass

from database.constants import NodeType
from database.utils import binary


@dataclass
class NodeData:
  """
  NodeData
  ========
  NodeData class represents a key-value pair in the B+Tree node. It contains
  the key, value, and the child node index.
  """
  key: bytes
  value: bytes
  child: int = 0


class BNode:
  """
  BNode
  =====
  BNode class represents a node in the B+Tree. It is a generic class that can
  represent both internal and leaf nodes. The class provides methods to
  serialize and deserialize the node, insert, update, and delete key-value
  pairs, split and merge nodes, and replace child nodes.
  """

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

  def __init__(self, ntype: NodeType):
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
    """
    Returns the type of the node. It can be either NodeType.LEAF or
    NodeType.INTERNAL.
    """
    return self._type

  @property
  def nkeys(self) -> int:
    """
    Returns the number of keys in the node.
    """
    return len(self._data)

  @property
  def total_bytes(self) -> int:
    """
    Returns the total number of bytes required to serialize the node.
    """
    return 2 + 2 + 8 * self.nkeys + sum(
        2 + 2 + len(x.key) + len(x.value) for x in self._data
    )

  def serialize(self) -> bytes:
    """
    Serializes the node into a byte string.
    """
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
    """
    Deserializes the byte string into a BNode object.
    """
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
    """
    Inserts a key-value pair at the specified index.
    """
    assert 0 <= index <= self.nkeys
    self._data.insert(index, NodeData(key, value))

  def set_child(self, index: int, child: int):
    """
    Sets the child node at the specified index.
    """
    self._data[index].child = child

  def get(self, index: int) -> NodeData:
    """
    Returns the key-value pair at the specified index.
    """
    return self._data[index]

  def get_child(self, index: int) -> int:
    """
    Returns the child node at the specified index.
    """
    return self._data[index].child

  def lookup_le(self, key: bytes) -> int:
    """
    Returns the index of the key that is less than or equal to the specified
    key.
    """
    found = 0
    for i in range(1, self.nkeys):
      if self.get(i).key > key:
        break
      found = i
    return found
