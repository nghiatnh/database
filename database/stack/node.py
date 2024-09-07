from dataclasses import dataclass

from database.btree.constants import NodeType
from database.utils import binary


@dataclass
class NodeData:
  key: bytes
  value: bytes
  child: int = 0


class Node:
  # Node structure:
  # |-------------|
  # | type | next |
  # | 1b   | 8b   |
  # |-------------|

  def __init__(self, next_node: int = 0) -> None:
    self._type = NodeType.FREE
    self._next = next_node

  def __repr__(self) -> str:
    return f"Node: {self.type.name}\n  Next: {self.next}"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def type(self) -> NodeType:
    return self._type

  @property
  def next(self) -> int:
    return self._next

  def serialize(self) -> bytes:
    return binary.bytes1(self.type.value) + binary.bytes8(self.next)

  @staticmethod
  def deserialize(data: bytes) -> "Node":
    node_type = NodeType(binary.uint8(data[:1]))
    assert node_type == NodeType.FREE
    return Node(binary.uint64(data[1:9]))

  def set_next(self, next_node: int) -> None:
    self._next = next_node
