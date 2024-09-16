import os
from typing import Optional, Dict
from pathlib import Path

from database.btree import node_factory
from database.btree import BNode
from database.btree import BTree
from database.kvstore.master_page import MasterPage
from database.kvstore.io import FileHandler
from database.constants import MASTER_SIG
from database.constants import PAGE_SIZE


class KVStore:
  def __init__(self, path: Path) -> None:
    self.tree = BTree(
        get_=self._page_get, new_=self._page_new, del_=self._page_del
    )
    self._file = FileHandler(path)
    self._version = 1
    self._flushed = 0
    self._added = 0
    self._updated: Dict[int, BNode] = {}

  @property
  def master_page(self) -> MasterPage:
    return MasterPage(
        sig=MASTER_SIG,
        version=self._version,
        flushed=self._flushed,
        root=self.tree.root
    )

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  # ------------------------------------------------------------------------- #
  # Callbacks for BTree                                                       #
  # ------------------------------------------------------------------------- #

  def _page_new(self, node: BNode) -> int:
    page_id = self._flushed + self._added
    self._updated[page_id] = node
    self._added += 1
    return page_id

  def _page_get(self, page_id: int) -> BNode:
    if page_id in self._updated:
      return self._updated[page_id]
    data = self._file.read(page_id * PAGE_SIZE, PAGE_SIZE)
    return node_factory(data)

  def _page_del(self, page_id: int) -> None:
    self._updated.pop(page_id, None)

  # ------------------------------------------------------------------------- #
  # Master Page                                                               #
  # ------------------------------------------------------------------------- #

  def _master_load(self) -> None:
    data = self._file.read(0, PAGE_SIZE)
    if len(data) == 0:
      self._version = 1
      self._flushed = 1
      self.tree.root = 0
      return
    master_page = MasterPage.deserialize(data)
    self._version = master_page.version
    self._flushed = master_page.flushed
    self.tree.root = master_page.root

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
    n_pages = self._flushed + self._added
    self._extend_file(n_pages)
    for page_id, node in self._updated.items():
      self._file.write(page_id * PAGE_SIZE, node.serialize())
    self._flushed = n_pages
    self._added = 0
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

  def insert(self, key: bytes, value: bytes) -> None:
    self.tree.insert(key, value)
    self._flush()

  def delete(self, key: bytes) -> None:
    self.tree.delete(key)
    self._flush()
