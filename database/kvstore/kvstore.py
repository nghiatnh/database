import os
from typing import Optional, Dict, Union
from pathlib import Path
from dataclasses import dataclass

from database.btree import BNode
from database.btree import LeafNode
from database.btree import InternalNode
from database.btree import BTree
from database.btree import SetRequest
from database.btree import SetResponse
from database.btree import DeleteRequest
from database.btree import DeleteResponse
from database.stack import StackNode
from database.stack import Stack
from database.kvstore.master_page import MasterPage
from database.kvstore.io import FileHandler
from database.utils import binary
from database.constants import NodeType
from database.constants import MASTER_SIG
from database.constants import PAGE_SIZE


Node = Union[BNode, StackNode]


def node_factory(data: bytes) -> Node:
  node_type = NodeType(binary.int16(data[:2]))
  if node_type == NodeType.LEAF:
    return LeafNode.deserialize(data)
  if node_type == NodeType.INTERNAL:
    return InternalNode.deserialize(data)
  return StackNode.deserialize(data)


@dataclass
class KVTX:
  root: int
  top: int


class KVStore:
  def __init__(self, path: Path) -> None:
    self.tree = BTree(
        get_=self._page_get, new_=self._page_new, del_=self._page_del
    )
    self.stack = Stack(
        new_=self._page_new, get_=self._page_get, use_=self._page_use
    )
    self._file = FileHandler(path)
    self._version = 1
    self._flushed = 0
    self._n_added = 0
    self._n_free = 0
    self._updated: Dict[int, Node] = {}
    self._tx: Optional[KVTX] = None

  @property
  def master_page(self) -> MasterPage:
    return MasterPage(
        sig=MASTER_SIG,
        version=self._version,
        flushed=self._flushed,
        root=self.tree.root,
        top=self.stack.top,
    )

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  # ------------------------------------------------------------------------- #
  # Callbacks for BTree and Stack                                             #
  # ------------------------------------------------------------------------- #

  def _page_new(self, node: Node) -> int:
    if self._n_free < self.stack.total_length:
      page_id = self.stack.get(self._n_free)
      self._updated[page_id] = node
      self._n_free += 1
      return page_id
    page_id = self._flushed + self._n_added
    self._updated[page_id] = node
    self._n_added += 1
    return page_id

  def _page_use(self, page_id: int, node: Node) -> None:
    self._updated[page_id] = node

  def _page_get(self, page_id: int) -> Node:
    if page_id in self._updated:
      return self._updated[page_id]
    data = self._file.read(page_id * PAGE_SIZE, PAGE_SIZE)
    return node_factory(data)

  def _page_del(self, page_id: int) -> None:
    self._updated[page_id] = None

  # ------------------------------------------------------------------------- #
  # Master Page                                                               #
  # ------------------------------------------------------------------------- #

  def _master_load(self) -> None:
    data = self._file.read(0, PAGE_SIZE)
    if len(data) == 0:
      self._version = 1
      self._flushed = 1
      self.tree.root = 0
      self.stack.top = 0
      self._updated.clear()
      return
    master_page = MasterPage.deserialize(data)
    self._version = master_page.version
    self._flushed = master_page.flushed
    self.tree.root = master_page.root
    self.stack.top = master_page.top
    self._updated.clear()

  def _master_save(self) -> None:
    self._file.write(0, self.master_page.serialize())
    self._file.flush()

  # ------------------------------------------------------------------------- #
  # Flushing                                                                  #
  # ------------------------------------------------------------------------- #

  def _extend_file(self, n_pages: int) -> None:
    if self._file.size < n_pages * PAGE_SIZE:
      self._file.extend(n_pages * PAGE_SIZE)

  def _flush(self) -> None:
    self.stack.update(
        self._n_free,
        [page_id for page_id, x in self._updated.items() if x is None]
    )
    n_pages = self._flushed + self._n_added
    self._extend_file(n_pages)
    for page_id, node in self._updated.items():
      if node is None:
        continue
      self._file.write(page_id * PAGE_SIZE, node.serialize())
    self._flushed = n_pages
    self._n_added = 0
    self._n_free = 0
    self._updated.clear()
    self._master_save()

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def open(self) -> None:
    try:
      if os.path.exists(self._file.path):
        self._file.open("r+b")
      else:
        self._file.open("w+b")
      self._master_load()
    except Exception as e:
      self.close()
      raise e

  def close(self) -> None:
    self._file.close()

  def get(self, key: bytes) -> Optional[bytes]:
    return self.tree.get(key)

  def set(self, req: SetRequest) -> SetResponse:
    res = self.tree.set(req)
    return res

  def delete(self, req: DeleteRequest) -> DeleteResponse:
    res = self.tree.delete(req)
    return res

  def begin(self):
    if self._tx is not None:
      raise ValueError("Transaction already started")
    self._tx = KVTX(root=self.tree.root, top=self.stack.top)

  def commit(self):
    if self._tx is None:
      raise ValueError("No transaction started")
    self._tx = None
    self._flush()

  def rollback(self):
    if self._tx is None:
      raise ValueError("No transaction started")
    self.tree.root = self._tx.root
    self.stack.top = self._tx.top
    self._tx = None
    self._n_free = 0
    self._n_added = 0
    self._updated.clear()
