import os
from typing import Dict, Optional, Union
from dataclasses import dataclass

from database.btree import BNode
from database.btree import BTree
from database.btree import InsertReq
from database.btree import DeleteReq
from database.btree import BIter
from database.free_list.node import FreeNode
from database.free_list import FreeList
from database.kvstore.io import FileHandler
from database.kvstore.master_page import MasterPage
from database.constants import CompareOP
from database.constants import PAGE_SIZE
from database.constants import MASTER_SIG


@dataclass
class KVTX:
  """
  KVTX
  ====
  KVTX class represents a transaction object. It contains the root and head
  pointers of the BTree and FreeList instances.
  """

  root: int
  head: int


class KVStore:
  """
  KVStore
  =======
  KVStore class represents the key-value store database. It provides methods to
  open and close the database file, begin and commit transactions, and access
  the BTree and FreeList instances.
  """

  def __init__(self, path: str):
    self._file: FileHandler = FileHandler(path)
    self._tree: BTree
    self._free_list: FreeList
    self._flushed: int = 0
    self._nappend: int = 0
    self._n_free: int = 0
    self._updates: Dict[int, Optional[Union[BNode, FreeNode]]] = {}

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  def _master_load(self):
    if self._file.size == 0:
      self._flushed = 1
      return
    master_page = MasterPage.deserialize(self._file.read(0, PAGE_SIZE))
    bad = not 1 <= master_page.used <= self._file.size / PAGE_SIZE
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

  # Callbacks for BTree, create a new page and return the index
  def _page_new(self, node: BNode) -> int:
    return self._new(node)

  # Callbacks for BTree, get the page at the given index
  def _page_get(self, index: int) -> BNode:
    if index in self._updates:
      res = self._updates[index]
      assert isinstance(res, BNode)
      return res
    data = self._file.read(index * PAGE_SIZE, PAGE_SIZE)
    return BNode.deserialize(data)

  # Callbacks for BTree, delete the page at the given index
  def _page_del(self, index: int):
    self._updates[index] = None

  # Callbacks for FreeList, create a new free node and return the index
  def _free_new(self, node: FreeNode) -> int:
    return self._new(node)

  # Callbacks for FreeList, reuse the free node at the given index
  def _free_use(self, index: int, node: FreeNode):
    self._updates[index] = node

  # Callbacks for FreeList, get the free node at the given index
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

  def _rollback(self, root: int, head: int):
    self._tree.root = root
    self._free_list.head = head
    self._n_free = 0
    self._nappend = 0
    self._updates.clear()

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def tree(self) -> BTree:
    """
    Returns the BTree instance.
    """
    return self._tree

  @property
  def free_list(self) -> FreeList:
    """
    Returns the FreeList instance.
    """
    return self._free_list

  def open(self):
    """
    Opens the KVStore file in read-write mode. If the file does not exist, it
    creates a new file.
    """
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

  def close(self):
    """
    Closes the KVStore file.
    """
    self._file.close()

  def begin(self) -> KVTX:
    """
    Begins a new transaction. It returns a new transaction object.
    """
    return KVTX(self._tree.root, self._free_list.head)

  def commit(self, tx: KVTX):
    """
    Commits the transaction. It writes the changes made during the transaction
    to the file.
    """
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
    """
    Aborts the transaction. It rolls back the changes made during the
    transaction.
    """
    self._rollback(tx.root, tx.head)

  def get(self, key: bytes) -> bytes:
    """
    Returns the value for the given key.
    """
    return self.tree.get(key)

  def update(self, req: InsertReq) -> bool:
    """
    Inserts or updates the key-value pair in the database.
    """
    self.tree.insert(req)
    return req.added

  def delete(self, req: DeleteReq) -> bool:
    """
    Deletes the key-value pair from the database for the given key.
    """
    return self.tree.delete(req)

  def seek(self, key: bytes, op: CompareOP) -> BIter:
    """
    Seeks the key in the database and returns an iterator.
    """
    return BIter.seek(self.tree, key, op)
