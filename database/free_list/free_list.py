from typing import Callable, List
import graphviz

from database.free_list.node import FreeNode
from database.constants import FREE_LIST_CAP


class FreeList:
  def __init__(self, head: int = 0) -> None:
    self.head: int = head
    # Callbacks
    self._new: Callable[[FreeNode], int]
    self._get: Callable[[int,], FreeNode]
    self._use: Callable[[int, FreeNode], None]

  @property
  def total_length(self) -> int:
    if self.head == 0:
      return 0
    return self._get(self.head).total_length

  def _push(self, freed: List[int], reuse: List[int]):
    while len(freed) > 0:
      size = min(len(freed), FREE_LIST_CAP)
      node = FreeNode(self.head)
      for child in freed[:size]:
        node.append(child)
      freed = freed[size:]
      if len(reuse) > 0:
        self.head = reuse[0]
        reuse = reuse[1:]
        self._use(self.head, node)
      else:
        self.head = self._new(node)
    assert len(reuse) == 0

  def _add_node(self, node: FreeNode, idx: int, dot: graphviz.Digraph):
    last = -1
    for i in range(node.length):
      child = node.get_child(i)
      if child != 0:
        if last != -1:
          dot.node(str(child))
          dot.edge(str(last), str(child))
        else:
          dot.node(str(child), f"Node {idx}\n{child}", shape="box")
        last = child
    if node.next != 0:
      next_node = self._get(node.next)
      self._add_node(next_node, node.next, dot)
      dot.edge(str(last), str(node.next))

  def render(self, filename: str):
    dot = graphviz.Digraph()
    self._add_node(self._get(self.head), self.head, dot)
    dot.render(filename, format="png", view=True)

  def set_callbacks(
      self,
      new: Callable[[FreeNode], int],
      get: Callable[[int,], FreeNode],
      use: Callable[[int, FreeNode], None],
  ):
    self._new = new
    self._get = get
    self._use = use

  def get(self, n: int) -> int:
    assert 0 <= n < self.total_length
    node = self._get(self.head)
    while node.length <= n:
      n -= node.length
      node = self._get(node.next)
    return node.get_child(node.length - n - 1)

  def update(self, n: int, freed: List[int]):
    assert 0 <= n <= self.total_length
    if n == 0 and len(freed) == 0:
      return
    total = self.total_length
    reuse = []
    while self.head != 0 and len(reuse) * FREE_LIST_CAP < len(freed):
      node = self._get(self.head)
      freed.append(self.head)
      if n >= node.length:
        n -= node.length
      else:
        remain = node.length - n
        n = 0
        while remain > 0 and len(reuse) * FREE_LIST_CAP < len(freed) + remain:
          remain -= 1
          reuse.append(node.get_child(remain))
        for i in range(remain):
          freed.append(node.get_child(i))
      total -= node.length
      self.head = node.next
    assert len(reuse) * FREE_LIST_CAP >= len(freed) or self.head == 0
    self._push(freed, reuse)
    self._get(self.head).set_total_length(total + len(freed))
