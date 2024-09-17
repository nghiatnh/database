from typing import List, Tuple
from dataclasses import dataclass

from database.btree.bnode import BNode
from database.btree.bnode import InternalNode
from database.btree.bnode import LeafNode
from database.btree.btree import BTree
from database.constants import CompareOP
from database.constants import COMPARE_FN


@dataclass
class PathData:
  node: BNode
  pos: int


class BIter:
  def __init__(self, tree: BTree) -> None:
    self.tree = tree
    self.path: List[PathData] = []
    self._is_valid = True

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  def _move_prev(self, level: int):
    if level == 0 and self.path[level].pos == 0:
      self._is_valid = False
      return
    if self.path[level].pos == 0:
      self._move_prev(level - 1)
    else:
      self.path[level].pos -= 1
    if level < len(self.path) - 1:
      cur_node = self.path[level].node
      assert isinstance(cur_node, InternalNode)
      node = self.tree.get_node_by_id(
          cur_node.children[self.path[level].pos]
      )
      self.path[level + 1] = PathData(node, node.n_keys - 1)

  def _move_next(self, level: int):
    n_keys = self.path[level].node.n_keys
    if level == 0 and self.path[level].pos == n_keys - 1:
      self._is_valid = False
      return
    if self.path[level].pos == self.path[level].node.n_keys - 1:
      self._move_next(level - 1)
    else:
      self.path[level].pos += 1
    if level < len(self.path) - 1:
      cur_node = self.path[level].node
      assert isinstance(cur_node, InternalNode)
      node = self.tree.get_node_by_id(
          cur_node.children[self.path[level].pos]
      )
      self.path[level + 1] = PathData(node, 0)

  @staticmethod
  def _seek_le(tree: BTree, key: bytes) -> "BIter":
    it = BIter(tree)
    node_id = tree.root
    while node_id != 0:
      node = tree.get_node_by_id(node_id)
      idx = node.lookup_le(key)
      it.path.append(PathData(node=node, pos=idx))
      if not isinstance(node, InternalNode):
        break
      node_id = node.children[idx]
    if len(it.path) > 0:
      assert isinstance(it.path[-1].node, LeafNode)
    return it

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def is_valid(self) -> bool:
    return len(self.path) > 0 and self._is_valid

  @staticmethod
  def seek(tree: BTree, key: bytes, op: CompareOP) -> "BIter":
    it = BIter._seek_le(tree, key)
    if it.is_valid and not COMPARE_FN[op](it.deref()[0], key):
      if op in [CompareOP.GE, CompareOP.GT]:
        it.move_next()
      else:
        it.move_prev()
    return it

  def deref(self) -> Tuple[bytes, bytes]:
    assert self.is_valid
    cur_node = self.path[-1].node
    assert isinstance(cur_node, LeafNode)
    return cur_node.keys[self.path[-1].pos], cur_node.values[self.path[-1].pos]

  def move_prev(self):
    self._move_prev(len(self.path) - 1)

  def move_next(self):
    self._move_next(len(self.path) - 1)
