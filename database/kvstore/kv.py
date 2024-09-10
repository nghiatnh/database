import os
from typing import Dict, Optional, Union

from database.btree import BNode
from database.btree import BTree
from database.free_list.node import FreeNode
from database.free_list import FreeList
from database.kvstore.io import FileHandler
from database.kvstore.master_page import MasterPage
from database.protocol import KVTX
from database.constants import PAGE_SIZE
from database.constants import MASTER_SIG


class KVStore:
  def __init__(self, path: str) -> None:
    self._file: FileHandler = FileHandler(path)
    self._tree: BTree
    self._free_list: FreeList
    self._flushed: int = 0
    self._nappend: int = 0
    self._n_free: int = 0
    self._updates: Dict[int, Optional[Union[BNode, FreeNode]]] = {}

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
    self._free_list.head = master_page.head
    self._flushed = master_page.used

  def _master_store(self):
    serialized = MasterPage(
        MASTER_SIG, self._tree.root, self._flushed, self._free_list.head
    ).serialize()
    self._file.write(0, serialized)

  def _new(self, node: Union[BNode, FreeNode]) -> int:
    assert node.total_bytes <= PAGE_SIZE
    if self._n_free < self._free_list.total_length:
      child = self._free_list.get(self._n_free)
      self._n_free += 1
    else:
      child = self._flushed + self._nappend
      self._nappend += 1
    self._updates[child] = node
    return child

  def _page_new(self, node: BNode) -> int:
    return self._new(node)

  def _page_get(self, index: int) -> BNode:
    if index in self._updates:
      res = self._updates[index]
      assert isinstance(res, BNode)
      return res
    data = self._file.read(index * PAGE_SIZE, PAGE_SIZE)
    return BNode.deserialize(data)

  def _page_del(self, index: int):
    self._updates[index] = None

  def _free_new(self, node: FreeNode) -> int:
    return self._new(node)

  def _free_use(self, index: int, node: FreeNode):
    self._updates[index] = node

  def _free_get(self, index: int) -> FreeNode:
    if index in self._updates:
      res = self._updates[index]
      assert isinstance(res, FreeNode)
      return res
    data = self._file.read(index * PAGE_SIZE, PAGE_SIZE)
    return FreeNode.deserialize(data)

  def _extend_file(self, n_pages: int):
    self._file.extend(n_pages * PAGE_SIZE)

  def _write_pages(self):
    freed = []
    for i, page in self._updates.items():
      if page is None:
        freed.append(i)
    self._free_list.update(self._n_free, freed)
    n_pages = self._flushed + self._nappend
    self._extend_file(n_pages)
    for i, page in self._updates.items():
      if page is not None:
        self._file.write(i * PAGE_SIZE, page.serialize())

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def tree(self) -> BTree:
    return self._tree

  @property
  def free_list(self) -> FreeList:
    return self._free_list

  def open(self):
    try:
      if os.path.exists(self._file.path):
        self._file.open("r+b")
      else:
        self._file.open("w+b")
      self._tree = BTree()
      self._free_list = FreeList()
      self._tree.set_callbacks(self._page_new, self._page_get, self._page_del)
      self._free_list.set_callbacks(
          self._free_new, self._free_get, self._free_use)
      self._master_load()
    except Exception as e:
      self.close()
      raise e

  def _rollback(self, root: int, head: int):
    self._tree.root = root
    self._free_list.head = head
    self._n_free = 0
    self._nappend = 0
    self._updates.clear()

  def close(self):
    self._file.close()

  def begin(self, tx: KVTX) -> KVTX:
    tx.db = self
    tx.root = self._tree.root
    tx.head = self._free_list.head
    return tx

  def commit(self, tx: KVTX):
    if tx.root == self.tree.root and tx.head == self.free_list.head:
      return
    try:
      self._write_pages()
    except Exception as e:
      self._rollback(tx.root, tx.head)
      raise e
    self._flushed = self._flushed + self._nappend
    self._nappend = 0
    self._n_free = 0
    self._updates.clear()
    self._master_store()
    self._file.flush()

  def abort(self, tx: KVTX):
    self._rollback(tx.root, tx.head)
