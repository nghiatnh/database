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
      del_: Callable[[int], None] = None
  ) -> None:
    self.top = 0
    # Callbacks
    self._new = new_
    self._get = get_
    self._del = del_

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

  def _push(self, total_length: int, new_children: List[int]):
    if self.top != 0:
      top = self._get(self.top)
      if top.n_children < STACK_CAP:
        new_children = new_children + [self.top]
      else:
        top = StackNode(next_node=self.top, children=[])
    else:
      top = StackNode(next_node=0, children=[])
    for child in new_children:
      top.children.append(child)
      self._del(child)
      if len(top.children) == STACK_CAP:
        self.top = self._new(top)
        top = StackNode(next_node=self.top, children=[])
      total_length += 1
    if len(top.children) > 0:
      self.top = self._new(top)
    self._get(self.top).total_length = total_length

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

  def update(self, n_used: int, new_children: List[int]) -> None:
    # Remove n_used elements from the stack
    if n_used == 0 and len(new_children) == 0:
      return
    total_length = self.total_length - n_used
    while n_used > 0 and self.top != 0:
      node = self._get(self.top)
      new_children = new_children + [self.top]
      if n_used >= node.n_children:
        n_used -= node.n_children
      else:
        new_children = node.children[:node.n_children-n_used] + new_children
        total_length -= node.n_children - n_used  # Will be added back
        n_used = 0
      self.top = node.next_node
    assert n_used == 0
    # Add new children to the stack
    self._push(total_length, new_children)

  def render(self, filename="stack.gv") -> None:
    dot = graphviz.Digraph()
    top = self._get(self.top)
    self._add_node(top, self.top, dot)
    dot.render(filename, format="png", cleanup=True, view=True)
