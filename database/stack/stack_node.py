from typing import List

from dataclasses import dataclass
from database.utils import binary
from database.constants import NodeType


@dataclass
class StackNode:
  # Stack node structure:
  # | Type | Next | Total Length | N Children | Children... |
  # | 2b   | 8b   | 8b           | 4b         | 8b * N      |

  type: NodeType = NodeType.FREE
  next_node: int = 0
  total_length: int = 0
  children: List[int] = None

  def __repr__(self):
    return f"Node({self.type.name}: {self.n_bytes} {self.children})"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def n_bytes(self) -> int:
    return 2 + 8 + 8 + 4 + 8 * self.n_children

  @property
  def n_children(self) -> int:
    return len(self.children)

  def serialize(self) -> bytes:
    data = (
        binary.bytes2(self.type.value) +
        binary.bytes8(self.next_node) +
        binary.bytes8(self.total_length) +
        binary.bytes4(self.n_children)
    )
    for child in self.children:
      data += binary.bytes8(child)
    return data

  @staticmethod
  def deserialize(data: bytes) -> "StackNode":
    node_type = NodeType(binary.int16(data[:2]))
    assert node_type == NodeType.FREE
    next_node = binary.int64(data[2:10])
    total_length = binary.int64(data[10:18])
    n_children = binary.int32(data[18:22])
    data = data[22:]

    children = []
    for _ in range(n_children):
      children.append(binary.int64(data[:8]))
      data = data[8:]

    return StackNode(node_type, next_node, total_length, children)
