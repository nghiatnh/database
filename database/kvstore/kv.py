import os
from typing import Dict, Optional

from database.btree import Node
from database.btree import BTree
from database.stack.node import Node as StackNode
from database.stack import Stack
from database.btree import PAGE_SIZE
from database.btree.constants import NodeType
from database.kvstore.io import FileHandler
from database.kvstore.master_page import MasterPage
from database.kvstore.constants import MASTER_SIG


class KVStore:
  def __init__(self, path: str) -> None:
    self._file: FileHandler = FileHandler(path)
    self._tree: BTree
    self._stack: Stack
    self._flushed: int = 0
    self._nappend: int = 0
    self._updates: Dict[int, Optional[Node]] = {}

  def _master_load(self):
    if self._file.size() == 0:
      self._flushed = 1
      return
    master_page = MasterPage.deserialize(self._file.read(0, PAGE_SIZE))
    bad = not 1 <= master_page.used <= self._file.size()/PAGE_SIZE
    bad = bad or not 0 <= master_page.root <= master_page.used
    if bad:
      raise ValueError("Bad master page")
    self._tree.root = master_page.root
    self._stack.top = master_page.top
    self._flushed = master_page.used

  def _master_store(self):
    serialized = MasterPage(
        MASTER_SIG, self._tree.root, self._flushed, self._stack.top
    ).serialize()
    self._file.write(0, serialized)

  def _page_new(self, node: Node) -> int:
    assert node.total_bytes <= PAGE_SIZE
    if self._stack.top > 0:
      idx = self._stack.top
      self._stack.pop()
      self._updates[idx] = node
      return idx
    child_id = self._flushed + self._nappend
    self._updates[child_id] = node
    self._nappend += 1
    return child_id

  def _page_get(self, index: int) -> Node:
    if index in self._updates:
      res = self._updates[index]
      assert res is not None
      return res
    return Node.deserialize(self._file.read(index * PAGE_SIZE, PAGE_SIZE))

  def _stack_get(self, index: int) -> StackNode:
    return StackNode.deserialize(self._file.read(index * PAGE_SIZE, PAGE_SIZE))

  def _page_del(self, index: int):
    self._updates[index] = None

  def _extend_file(self, n_pages: int):
    self._file.extend(n_pages * PAGE_SIZE)

  def _flush(self):
    n_pages = self._flushed + self._nappend
    self._extend_file(n_pages)
    stack: Dict[int, StackNode] = {}
    for i, node in self._updates.items():
      if node is None:
        stack[i] = self._stack.push(i)
        continue
      assert node.type in [NodeType.INTERNAL, NodeType.LEAF]
      self._file.write(i * PAGE_SIZE, node.serialize())
    for i, node in stack.items():
      assert node.type == NodeType.FREE
      self._file.write(i * PAGE_SIZE, node.serialize())
    self._flushed = n_pages
    self._nappend = 0
    self._updates.clear()
    self._master_store()
    self._file.flush()

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def open(self):
    try:
      if os.path.exists(self._file.path):
        self._file.open('r+b')
      else:
        self._file.open('w+b')
      self._tree = BTree()
      self._stack = Stack()
      self._tree.set_callbacks(self._page_new, self._page_get, self._page_del)
      self._stack.set_callbacks(self._stack_get)
      self._master_load()
    except Exception as e:
      self.close()
      raise e

  def close(self):
    self._file.close()

  def get(self, key: bytes) -> bytes:
    return self._tree.get(key)

  def set(self, key: bytes, value: bytes):
    self._tree.insert(key, value)
    self._flush()

  def delete(self, key: bytes) -> bool:
    success = self._tree.delete(key)
    if success:
      self._flush()
    return success
