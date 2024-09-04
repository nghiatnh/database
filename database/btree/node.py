from abc import ABC, abstractmethod
from typing import List

from database.btree.constants import NodeType
from database.utils import binary


class Node(ABC):
  """
  Node
  ====
  Node is an abstract class that represents a node in the B+ tree.
  """

  def __init__(self, node_type: NodeType) -> None:
    self._type = node_type

  @property
  def type(self) -> NodeType:
    """
    Return the type of the node.
    """
    return self._type

  @property
  @abstractmethod
  def n_keys(self) -> int:
    """
    Return the number of keys in the node.
    """

  @property
  @abstractmethod
  def total_bytes(self) -> int:
    """
    Return the total number of bytes required to serialize the node.
    """

  @abstractmethod
  def serialize(self) -> bytes:
    """
    Serialize the node to bytes.
    """

  @staticmethod
  @abstractmethod
  def deserialize(data: bytes) -> "Node":
    """
    Deserialize the node from bytes.
    """


class LeafNode(Node):
  """
  LeafNode
  ========
  LeafNode represents a leaf node in the B+ tree.
  """

  # Node structure:
  # |-------------------------------|
  # | type | n_keys  | key-value... |
  # | 1b   | 8b      | ...          |
  # |-------------------------------|
  #
  # Key-value structure:
  # |-----------------------------------------|
  # | key length | value length | key | value |
  # | 2b         | 2b           | ... | ...   |
  # |-----------------------------------------|

  def __init__(self) -> None:
    super().__init__(NodeType.LEAF)
    self._keys: List[bytes] = []
    self._values: List[bytes] = []

  def __repr__(self) -> str:
    pairs = "\n  ".join(
        f"{key}: {value} "for key, value in zip(self._keys, self._values)
    )
    return f"LeafNode:\n  {pairs}"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def n_keys(self) -> int:
    return len(self._keys)

  @property
  def total_bytes(self) -> int:
    return 1 + 8 + sum(
        2 + 2 + len(k) + len(v) for k, v in zip(self._keys, self._values)
    )

  def serialize(self) -> bytes:
    data = binary.bytes1(self.type.value) + binary.bytes8(self.n_keys)
    for key, value in zip(self._keys, self._values):
      data += binary.bytes2(len(key)) + binary.bytes2(len(value)) + key + value
    return data

  @staticmethod
  def deserialize(data: bytes) -> "LeafNode":
    node_type = NodeType(binary.uint8(data[:1]))
    assert node_type == NodeType.LEAF
    node = LeafNode()
    n_keys = binary.uint64(data[1:9])
    data = data[9:]
    for i in range(n_keys):
      key_length = binary.uint16(data[:2])
      value_length = binary.uint16(data[2:4])
      node.insert(
          i,
          data[4: 4 + key_length],
          data[4 + key_length: 4 + key_length + value_length],
      )
      data = data[4 + key_length + value_length:]
    return node

  def insert(self, index: int, key: bytes, value: bytes) -> None:
    """
    Insert a key-value pair at the specified index.
    """
    assert 0 <= index <= len(self._keys)
    self._keys.insert(index, key)
    self._values.insert(index, value)


class InternalNode(Node):
  """
  InternalNode
  ============
  InternalNode represents an internal node in the B+ tree
  """

  # Node structure:
  # |----------------------------------------------|
  # | type | n_keys  | n_child | child... | key... |
  # | 1b   | 8b      | 8b      | ...      | ...    |
  # |----------------------------------------------|
  #
  # Child structure:
  # |----------|
  # | child id |
  # | 8b       |
  # |----------|
  #
  # Key structure:
  # |------------------|
  # | key length | key |
  # | 2b         | ... |
  # |------------------|

  def __init__(self) -> None:
    super().__init__(NodeType.INTERNAL)
    self._children: List[int] = []
    self._keys: List[bytes] = []

  def __repr__(self) -> str:
    children = ", ".join(str(child) for child in self._children)
    keys = ", ".join(str(key) for key in self._keys)
    return f"InternalNode:\n  Children: {children}\n  Keys: {keys}"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def n_keys(self) -> int:
    return len(self._keys)

  @property
  def n_child(self) -> int:
    """
    Return the number of children in the node.
    """
    return len(self._children)

  @property
  def total_bytes(self) -> int:
    return 1 + 8 + 8 + 8 * len(self._children) + sum(
        2 + len(k) for k in self._keys
    )

  def serialize(self) -> bytes:
    data = binary.bytes1(self.type.value)
    data += binary.bytes8(self.n_keys) + binary.bytes8(self.n_child)
    for child in self._children:
      data += binary.bytes8(child)
    for key in self._keys:
      data += binary.bytes2(len(key)) + key
    return data

  @staticmethod
  def deserialize(data: bytes) -> "InternalNode":
    node_type = NodeType(binary.uint8(data[:1]))
    assert node_type == NodeType.INTERNAL
    node = InternalNode()
    n_keys = binary.uint64(data[1:9])
    n_child = binary.uint64(data[9:17])
    data = data[17:]
    for i in range(n_child):
      child_id = binary.uint64(data[:8])
      node.insert_child(i, child_id)
      data = data[8:]
    for i in range(n_keys):
      key_length = binary.uint16(data[:2])
      node.insert_key(i, data[2: 2 + key_length])
      data = data[2 + key_length:]
    return node

  def insert_child(self, index: int, child_id: int) -> None:
    """
    Insert a child at the specified index.
    """
    assert 0 <= index <= len(self._children)
    self._children.insert(index, child_id)

  def insert_key(self, index: int, key: bytes) -> None:
    """
    Insert a key at the specified index.
    """
    assert 0 <= index <= len(self._keys)
    self._keys.insert(index, key)
