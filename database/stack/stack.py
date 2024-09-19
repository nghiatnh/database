from typing import Callable, List
import graphviz

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
    # Callbacks
    self._new = new_
    self._get = get_
    self._use = use_

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  def _add_node(self, node: StackNode, idx: int, dot: graphviz.Digraph):
    last = -1
    for child_id in node.children:
      if last == -1:
        dot.node(str(child_id), label=f"{idx}: {child_id}")
      else:
        dot.node(str(child_id), label=f"{child_id}")
      if last != -1:
        dot.edge(str(last), str(child_id))
      last = child_id
    if node.next_node != 0:
      next_node = self._get(node.next_node)
      self._add_node(next_node, node.next_node, dot)
      if last != -1 and next_node.n_children > 0:
        dot.edge(str(last), str(next_node.children[0]))

  def _push(self, freed: List[int], reuse: List[int]):
    while len(freed) > 0:
      size = min(len(freed), STACK_CAP)
      node = StackNode(next_node=self.top, children=[])
      for child in freed[:size]:
        node.children.append(child)
      freed = freed[size:]
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
    return self._get(self.top).total_length

  def get(self, idx: int) -> int:
    if self.top == 0:
      raise ValueError("Stack is empty")

    top = self._get(self.top)
    while idx >= top.n_children:
      idx -= top.n_children
      if top.next_node == 0:
        raise IndexError("Index out of range")
      top = self._get(top.next_node)
    return top.children[top.n_children-idx-1]

  def update(self, n_used: int, freed: List[int]) -> None:
    assert 0 <= n_used <= self.total_length

    if n_used == 0 and len(freed) == 0:
      return

    total = self.total_length
    reuse = []
    while self.top != 0 and len(reuse) * STACK_CAP < len(freed):
      node = self._get(self.top)
      freed.append(self.top)
      if n_used >= node.n_children:
        n_used -= node.n_children
      else:
        remain = node.n_children - n_used
        n_used = 0
        while remain > 0 and len(reuse) * STACK_CAP < len(freed) + remain:
          remain -= 1
          reuse.append(node.children[remain])
        for i in range(remain):
          freed.append(node.children[i])
      total -= node.n_children
      self.top = node.next_node
    assert len(reuse) * STACK_CAP >= len(freed) or self.top == 0
    self._push(freed, reuse)
    self._get(self.top).total_length = total + len(freed)

  def render(self, filename="stack.gv") -> None:
    dot = graphviz.Digraph()
    top = self._get(self.top)
    self._add_node(top, self.top, dot)
    dot.render(filename, format="png", cleanup=True, view=True)
