from typing import List, Tuple

from database.btree.node import BNode
from database.btree.btree import BTree
from database.constants import NodeType
from database.constants import CompareOP
from database.constants import COMPARE_FUNC


class BIter:
  def __init__(self, tree: BTree) -> None:
    self._tree: BTree = tree
    self.path: List[BNode] = []
    self.pos: List[int] = []
    self._valid = True

  def _iter_prev(self, level: int):
    if self.pos[level] > 0:
      self.pos[level] -= 1
    elif level > 0:
      self._iter_prev(level - 1)
    else:
      self._valid = False
      return
    if level + 1 < len(self.pos):
      node = self.path[level]
      child = self._tree._get(node.get_child(self.pos[level]))
      self.path[level + 1] = child
      self.pos[level + 1] = child.nkeys - 1

  def _iter_next(self, level: int):
    if self.pos[level] < self.path[level].nkeys - 1:
      self.pos[level] += 1
    elif level > 0:
      self._iter_next(level - 1)
    else:
      self._valid = False
      return
    if level + 1 < len(self.pos):
      node = self.path[level]
      child = self._tree._get(node.get_child(self.pos[level]))
      self.path[level + 1] = child
      self.pos[level + 1] = 0

  @staticmethod
  def _seek_le(tree: BTree, key: bytes) -> "BIter":
    it = BIter(tree)
    child = tree.root
    while child != 0:
      node = tree._get(child)
      idx = node.lookup_le(key)
      it.path.append(node)
      it.pos.append(idx)
      child = node.get_child(idx) if node.type == NodeType.INTERNAL else 0
    return it

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def deref(self) -> Tuple[bytes, bytes]:
    data = self.path[-1].get(self.pos[-1])
    return data.key, data.value

  def valid(self) -> bool:
    return len(self.pos) > 0 and self._valid

  def prev(self):
    self._iter_prev(len(self.path) - 1)

  def next(self):
    self._iter_next(len(self.path) - 1)

  @staticmethod
  def seek(tree: BTree, key: bytes, op: CompareOP) -> "BIter":
    it = BIter._seek_le(tree, key)
    if op != CompareOP.LE and it.valid():
      cur, _ = it.deref()
      if not COMPARE_FUNC[op](cur, key):
        if op in [CompareOP.GE, CompareOP.GT]:
          it.next()
        else:
          it.prev()
    return it
