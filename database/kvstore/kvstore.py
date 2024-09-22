import os
from typing import Optional, Dict, Union, List
from pathlib import Path
from dataclasses import dataclass
import json

import filelock

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


class TransactionError(Exception):
  pass


@dataclass
class KVData:
  root: int
  top: int
  flushed: int
  version: int
  readers: List[int]

  def to_dict(self) -> dict:
    return {
        "root": self.root,
        "top": self.top,
        "flushed": self.flushed,
        "version": self.version,
        "readers": self.readers
    }

  @staticmethod
  def from_dict(data: dict) -> "KVData":
    return KVData(
        root=data["root"],
        top=data["top"],
        flushed=data["flushed"],
        version=data["version"],
        readers=data["readers"]
    )


class KVStore:
  def __init__(self, path: Path) -> None:
    self.data_file = "kvtx_data.json"
    self.lock = filelock.FileLock("process.lock")
    self.writer = filelock.FileLock("writer.lock")
    self._file = FileHandler(path)
    self._path = path

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  def _read_data(self) -> KVData:
    with self.lock:
      with open(self.data_file, "r", encoding="utf-8") as f:
        return KVData.from_dict(json.load(f))

  def _write_data(self, data: KVData) -> None:
    with self.lock:
      with open(self.data_file, "w", encoding="utf-8") as f:
        json.dump(data.to_dict(), f)

  # ------------------------------------------------------------------------- #
  # Master Page                                                               #
  # ------------------------------------------------------------------------- #

  def _master_load(self) -> None:
    data = self._file.read(0, PAGE_SIZE)
    if len(data) == 0:
      tx_data = KVData(root=0, top=0, flushed=1, version=1, readers=[])
      self._write_data(tx_data)
      return
    master_page = MasterPage.deserialize(data)
    tx_data = KVData(
        root=master_page.root,
        top=master_page.top,
        flushed=master_page.flushed,
        version=master_page.version,
        readers=[]
    )
    self._write_data(tx_data)

  def _master_save(self) -> None:
    self._file.write(0, self.master_page.serialize())
    self._file.flush()

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def master_page(self) -> MasterPage:
    data = self._read_data()
    return MasterPage(
        sig=MASTER_SIG,
        version=data.version,
        flushed=data.flushed,
        root=data.root,
        top=data.top,
    )

  def begin_read(self, tx: "KVTX") -> None:
    tx.file = FileHandler(self._path)
    tx.file.open("r+b")
    with self.lock:
      data = self._read_data()
      tx.tree.root = data.root
      tx.stack.top = data.top
      tx.flushed = data.flushed
      tx.version = data.version
      data.readers.append(tx.version)
      self._write_data(data)
      tx.in_tx = True

  def end_read(self, tx: "KVTX") -> None:
    with self.lock:
      data = self._read_data()
      data.readers.remove(tx.version)
      self._write_data(data)
    tx.in_tx = False
    tx.file.close()

  def begin(self, tx: "KVTX") -> None:
    self.writer.acquire()
    tx.file = FileHandler(self._path)
    tx.file.open("r+b")
    with self.lock:
      data = self._read_data()
      tx.tree.root = data.root
      tx.stack.top = data.top
      tx.flushed = data.flushed
      tx.version = data.version
      tx.in_tx = True
      readers = data.readers
      if len(readers) > 0:
        minversion = min(x for x in readers)
      else:
        minversion = tx.version
      tx.stack.load(tx.stack.top, tx.version, minversion)

  def commit(self, tx: "KVTX") -> None:
    tx.flush()
    with self.lock:
      data = self._read_data()
      data.root = tx.tree.root
      data.top = tx.stack.top
      data.version = tx.version
      data.flushed = tx.flushed
      self._write_data(data)
    self._master_save()
    self.writer.release()
    tx.in_tx = False
    tx.file.close()

  def rollback(self, tx: "KVTX") -> None:
    with self.lock:
      data = self._read_data()
      tx.tree.root = data.root
      tx.stack.top = data.top
      tx.version = data.version
      tx.flushed = data.flushed
    self.writer.release()
    tx.in_tx = False
    tx.file.close()

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


class KVTX:
  def __init__(self) -> None:
    self.tree = BTree(
        get_=self._page_get, new_=self._page_new, del_=self._page_del
    )
    self.stack = Stack(
        new_=self._page_new, get_=self._page_get, use_=self._page_use
    )
    self.file: FileHandler = None
    self.version = 1
    self.flushed = 0
    self.in_tx = False
    self._n_added = 0
    self._n_free = 0
    self._updated: Dict[int, Node] = {}

  @property
  def master_page(self) -> MasterPage:
    return MasterPage(
        sig=MASTER_SIG,
        version=self.version,
        flushed=self.flushed,
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
    page_id = self.stack.pop()
    if page_id != 0:
      self._updated[page_id] = node
      return page_id
    page_id = self.flushed + self._n_added
    self._updated[page_id] = node
    self._n_added += 1
    return page_id

  def _page_use(self, page_id: int, node: Node) -> None:
    self._updated[page_id] = node

  def _page_get(self, page_id: int) -> Node:
    if page_id in self._updated:
      return self._updated[page_id]
    data = self.file.read(page_id * PAGE_SIZE, PAGE_SIZE)
    return node_factory(data)

  def _page_del(self, page_id: int) -> None:
    self._updated[page_id] = None

  # ------------------------------------------------------------------------- #
  # Flushing                                                                  #
  # ------------------------------------------------------------------------- #

  def _extend_file(self, n_pages: int) -> None:
    if self.file.size < n_pages * PAGE_SIZE:
      self.file.extend(n_pages * PAGE_SIZE)

  def flush(self) -> None:
    self.stack.save(
        [page_id for page_id, x in self._updated.items() if x is None]
    )
    n_pages = self.flushed + self._n_added
    self._extend_file(n_pages)
    for page_id, node in self._updated.items():
      if node is None:
        continue
      self.file.write(page_id * PAGE_SIZE, node.serialize())
    self.flushed = n_pages
    self.version += 1
    self._n_added = 0
    self._n_free = 0
    self._updated.clear()
    self.file.flush()

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def get(self, key: bytes) -> Optional[bytes]:
    if not self.in_tx:
      raise TransactionError("Transaction not started")
    return self.tree.get(key)

  def set(self, req: SetRequest) -> SetResponse:
    if not self.in_tx:
      raise TransactionError("Transaction not started")
    res = self.tree.set(req)
    return res

  def delete(self, req: DeleteRequest) -> DeleteResponse:
    if not self.in_tx:
      raise TransactionError("Transaction not started")
    res = self.tree.delete(req)
    return res
