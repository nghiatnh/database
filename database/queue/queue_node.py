from typing import List

from dataclasses import dataclass
from database.utils import binary
from database.constants import NodeType


@dataclass
class NodeData:
  """
  NodeData
  ========
  NodeData is a dataclass that represents the data stored in a node of
  the queue.
  """

  version: int
  value: int


@dataclass
class QueueNode:
  """
  QueueNode
  =========
  QueueNode is a dataclass that represents a node in the queue.
  """

  # Queue node structure:
  # | Type | Next | N Children | Version-Children Pair... |
  # | 2b   | 8b   | 4b         | 16b * N                  |

  type: NodeType = NodeType.FREE
  next_node: int = 0
  children: List[NodeData] = None

  def __repr__(self):
    return f"Node({self.type.name}: {self.n_bytes} {self.children})"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def n_bytes(self) -> int:
    """
    The number of bytes required to store the node in the database.
    """
    return 2 + 8 + 4 + 16 * self.n_children

  @property
  def n_children(self) -> int:
    """
    Number of children in the node.
    """
    return len(self.children)

  def serialize(self) -> bytes:
    """
    Serialize the node to bytes.
    """
    data = (
        binary.bytes2(self.type.value) +
        binary.bytes8(self.next_node) +
        binary.bytes4(self.n_children)
    )
    for child in self.children:
      data += binary.bytes8(child.version) + binary.bytes8(child.value)
    return data

  @staticmethod
  def deserialize(data: bytes) -> "QueueNode":
    """
    Deserialize the node from bytes.
    """
    node_type = NodeType(binary.int16(data[:2]))
    assert node_type == NodeType.FREE
    next_node = binary.int64(data[2:10])
    n_children = binary.int32(data[10:14])
    data = data[14:]

    children = []
    for _ in range(n_children):
      children.append(
          NodeData(
              version=binary.int64(data[:8]),
              value=binary.int64(data[8:16])
          )
      )
      data = data[16:]

    return QueueNode(node_type, next_node, children)
