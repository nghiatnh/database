from database.constants import NodeType
from database.utils import binary


class FreeNode:
  # FreeNode structure:
  # |---------------------------------------------------|
  # | type | length | total length | next | children... |
  # | 2b   | 2b     | 8b           | 8b   | 8b * length |
  # |---------------------------------------------------|

  def __init__(self, next_node: int = 0, total_length: int = 0) -> None:
    self._type = NodeType.FREE
    self._next = next_node
    self._children = []
    self._total_length = total_length

  def __repr__(self) -> str:
    child_str = "Children: " + ", ".join(str(x) for x in self._children)
    return f"Node: {self.type.name}\n  Next: {self.next}\n  {child_str}"

  def __str__(self) -> str:
    return self.__repr__()

  @property
  def type(self) -> NodeType:
    return self._type

  @property
  def length(self) -> int:
    return len(self._children)

  @property
  def total_length(self) -> int:
    return self._total_length

  @property
  def next(self) -> int:
    return self._next

  @property
  def total_bytes(self) -> int:
    return 2 + 2 + 8 + 8 + 8 * self.length

  def serialize(self) -> bytes:
    data = binary.bytes2(self.type.value) + binary.bytes2(self.length)
    data += binary.bytes8(self.total_length) + binary.bytes8(self.next)
    for child in self._children:
      data += binary.bytes8(child)
    return data

  @staticmethod
  def deserialize(data: bytes) -> "FreeNode":
    node_type = NodeType(binary.uint16(data[:2]))
    assert node_type == NodeType.FREE
    length = binary.uint16(data[2:4])
    total_length = binary.uint64(data[4:12])
    next_node = binary.uint64(data[12:20])
    node = FreeNode(next_node, total_length)
    data = data[20:]
    for _ in range(length):
      node.append(binary.uint64(data[:8]))
      data = data[8:]
    return node

  def append(self, child: int):
    self._children.append(child)

  def get_child(self, index: int) -> int:
    return self._children[index]

  def set_next(self, next_node: int) -> None:
    self._next = next_node

  def set_total_length(self, total_length: int):
    self._total_length = total_length
