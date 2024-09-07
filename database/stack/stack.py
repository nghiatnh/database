from typing import Callable
import graphviz

from database.stack.node import Node
from database.btree.constants import NodeType


class Stack:
  def __init__(self, top: int = 0) -> None:
    self.top: int = top
    # Callbacks
    self._get: Callable[[int,], Node]

  def _add_node(self, node: Node, idx: int, dot: graphviz.Digraph):
    dot.node(str(idx), f"{idx} ({node.type.name})")
    if node.next != 0:
      next_node = self._get(node.next)
      self._add_node(next_node, node.next, dot)
      dot.edge(str(idx), str(node.next))

  def render(self, filename: str):
    dot = graphviz.Digraph()
    self._add_node(self._get(self.top), self.top, dot)
    dot.render(filename, format="png", view=True)

  def set_callbacks(
      self,
      get: Callable[[int,], Node],
  ):
    self._get = get

  def push(self, index: int) -> Node:
    node = Node(self.top)
    self.top = index
    return node

  def pop(self) -> Node:
    node = self._get(self.top)
    assert node.type == NodeType.FREE
    self.top = node.next
    return node
