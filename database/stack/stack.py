from typing import Callable, List
import graphviz

from database.stack.stack_node import NodeData
from database.stack.stack_node import StackNode
from database.constants import STACK_CAP


class Stack:
  def __init__(
      self,
      *,
      new_: Callable[[StackNode], int] = None,
      get_: Callable[[int], StackNode] = None,
      use_: Callable[[int, StackNode], None] = None,
  ) -> None:
    self.top = 0
    self.version = 0
    self.min_version = 0
    self.offset = 0
    self.nodes = []
    # Callbacks
    self._new = new_
    self._get = get_
    self._use = use_

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  def _save(self, nodes: List[NodeData], reuse: List[int]):
    self.top = 0
    while len(nodes) > 0:
      size = min(len(nodes), STACK_CAP)
      node = StackNode(next_node=self.top, children=nodes[:size])
      nodes = nodes[size:]
      if len(reuse) > 0:
        self.top = reuse[0]
        reuse = reuse[1:]
        self._use(self.top, node)
      else:
        self.top = self._new(node)
    assert len(reuse) == 0

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def total_length(self) -> int:
    if self.top == 0:
      return 0
    return len(self.nodes)

  def load(self, top: int, version: int, min_version: int) -> None:
    self.top = top
    self.version = version
    self.min_version = min_version
    self.offset = 0
    self.nodes = []
    while top != 0:
      node = self._get(top)
      self.nodes = node.children + self.nodes
      top = node.next_node

  def pop(self) -> int:
    if self.top == 0 or self.offset >= self.total_length:
      return 0
    node = self.nodes[self.offset]
    if node.version < self.min_version:
      self.offset += 1
      return node.value
    return 0

  def save(self, freed: List[int]):
    if len(freed) == 0:
      return
    freed.append(self.top)
    offset = self.offset
    while True:
      self.offset = offset
      r = 1
      n_groups = (
          self.total_length - self.offset + len(freed) - 1) // STACK_CAP + 1
      reuse = []
      while r != 0 and len(reuse) < n_groups:
        r = self.pop()
        if r != 0:
          reuse.append(r)
      new_n_groups = (
          self.total_length - self.offset + len(freed) - 1) // STACK_CAP + 1
      if new_n_groups == n_groups:
        break
    nodes = self.nodes[self.offset:] + [
        NodeData(self.version, x) for x in freed
    ]
    self._save(nodes, reuse)
    self.nodes = nodes

  def render(self, filename="stack.gv") -> None:
    dot = graphviz.Digraph()
    top = self._get(self.top)
    last = -1
    for child in top.children:
      dot.node(str(child.value), label=f"{child.value}\n(v{child.version})")
      if last != -1:
        dot.edge(str(last), str(child.value))
      last = child.value
    dot.render(filename, format="png", cleanup=True, view=True)
