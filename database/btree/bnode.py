from typing import List
from dataclasses import dataclass

from database.utils import binary
from database.constants import NodeType


@dataclass
class BNode:
  """
  BNode
  =====
  BNode class represents a node in the BTree.
  """

  type: NodeType = NodeType.NULL
  keys: List[bytes] = None

  def __repr__(self):
    keys_str = "\n\t".join(str(k[:5]) for k in self.keys)
    return f"Node({self.type.name}: {self.n_bytes}\n\t{keys_str})"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def n_bytes(self) -> int:
    """
    The number of bytes required to store the node in the database.
    """

  @property
  def n_keys(self) -> int:
    """
    Number of keys in the node.
    """
    return len(self.keys)

  def serialize(self) -> bytes:
    """
    Serialize the node to bytes.
    """

  @staticmethod
  def deserialize(data: bytes) -> "BNode":
    """
    Deserialize the node from bytes.
    """

  def lookup_le(self, key: bytes) -> int:
    """
    Find the index of the key that is less than or equal to the given key.
    """
    found = 0
    for i, k in enumerate(self.keys):
      if key >= k:
        found = i
    return found


@dataclass
class LeafNode(BNode):
  """
  LeafNode
  ========
  LeafNode class represents a leaf node in the BTree.
  """

  # Leaf node structure:
  # | NodeType | N Keys | Key-Value Pair... |
  # | 2b       | 4b     | ...               |
  #
  # Key-Value Pair structure:
  # | Key Length | Value Length | Key | Value |
  # | 2b         | 2b           | ... | ...   |

  type: NodeType = NodeType.LEAF
  values: List[bytes] = None

  def __repr__(self):
    keys_str = "\n\t".join(str(k[:5]) for k in self.keys)
    return f"Node({self.type.name}: {self.n_bytes}\n\t{keys_str})"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def n_bytes(self) -> int:
    return 2 + 4 + sum(
        2 + 2 + len(k) + len(v) for k, v in zip(self.keys, self.values)
    )

  def serialize(self) -> bytes:
    data = binary.bytes2(self.type.value) + binary.bytes4(self.n_keys)
    for k, v in zip(self.keys, self.values):
      data += (
          binary.bytes2(len(k)) + binary.bytes2(len(v)) + k + v
      )
    return data

  @staticmethod
  def deserialize(data: bytes) -> "LeafNode":
    node_type = NodeType(binary.int16(data[:2]))
    assert node_type == NodeType.LEAF
    n_keys = binary.int32(data[2:6])
    data = data[6:]

    keys, values = [], []
    for _ in range(n_keys):
      key_len = binary.int16(data[:2])
      value_len = binary.int16(data[2:4])
      key = data[4:4 + key_len]
      value = data[4 + key_len:4 + key_len + value_len]
      keys.append(key)
      values.append(value)
      data = data[4 + key_len + value_len:]

    return LeafNode(node_type, keys, values)


@dataclass
class InternalNode(BNode):
  """
  InternalNode
  ============
  InternalNode class represents an internal node in the BTree.
  """

  # Internal node structure:
  # | NodeType | N Keys | Children... | Keys... |
  # | 2b       | 4b     | 8b * N Keys | ...     |
  #
  # Keys structure:
  # | Key Length | Key |
  # | 2b         | ... |

  type: NodeType = NodeType.INTERNAL
  children: List[int] = None

  def __repr__(self):
    keys_str = "\n\t".join(str(k[:5]) for k in self.keys)
    return f"Node({self.type.name}: {self.n_bytes}\n\t{keys_str})"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def n_bytes(self) -> int:
    return 2 + 4 + 8 * self.n_keys + sum(2 + len(k) for k in self.keys)

  def serialize(self) -> bytes:
    data = binary.bytes2(self.type.value) + binary.bytes4(self.n_keys)
    for child in self.children:
      data += binary.bytes8(child)
    for key in self.keys:
      data += binary.bytes2(len(key)) + key
    return data

  @staticmethod
  def deserialize(data: bytes) -> "InternalNode":
    node_type = NodeType(binary.int16(data[:2]))
    assert node_type == NodeType.INTERNAL
    n_keys = binary.int32(data[2:6])
    data = data[6:]

    children = [binary.int64(data[i:i + 8]) for i in range(0, n_keys * 8, 8)]
    data = data[n_keys * 8:]

    keys = []
    for _ in range(n_keys):
      key_len = binary.int16(data[:2])
      key = data[2:2 + key_len]
      keys.append(key)
      data = data[2 + key_len:]

    return InternalNode(node_type, keys, children)
