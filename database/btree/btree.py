from typing import Callable, List, Tuple
from dataclasses import dataclass
import graphviz

from database.btree.node import BNode
from database.btree.constants import MergeDir
from database.constants import UpdateMode
from database.constants import NodeType
from database.constants import PAGE_SIZE
from database.constants import MAX_KEY_SIZE
from database.constants import MAX_VALUE_SIZE


@dataclass
class InsertReq:
  key: bytes
  value: bytes
  mode: UpdateMode
  added: bool = False
  updated: bool = False
  old: bytes = b""


@dataclass
class DeleteReq:
  key: bytes
  deleted: bool = False
  old: bytes = b""


class BTree:
  def __init__(self, root: int = 0) -> None:
    self.root: int = root
    # Callbacks
    self._get: Callable[[int,], BNode]
    self._new: Callable[[BNode,], int]
    self._del: Callable[[int,], None]

  def _add_node(self, node: BNode, idx: int, dot: graphviz.Digraph):
    dot.node(str(idx), f"{idx} ({node.type.name}): {node.get(0).key[:5]}")
    for i in range(node.nkeys):
      child = node.get_child(i)
      if child != 0:
        self._add_node(self._get(child), child, dot)
        dot.edge(str(idx), str(child))

  def _should_merge(
      self,
      node: BNode,
      index: int,
      updated: BNode,
  ) -> Tuple[MergeDir, BNode]:
    if updated.total_bytes > PAGE_SIZE / 4:
      return MergeDir.NONE, BNode(NodeType.NULL)
    if index > 0:
      sibling = self._get(node.get_child(index - 1))
      merged = sibling.total_bytes + updated.total_bytes - 4
      if merged <= PAGE_SIZE:
        return MergeDir.LEFT, sibling
    if index + 1 < node.nkeys:
      sibling = self._get(node.get_child(index + 1))
      merged = sibling.total_bytes + updated.total_bytes - 4
      if merged <= PAGE_SIZE:
        return MergeDir.RIGHT, sibling
    return MergeDir.NONE, BNode(NodeType.NULL)

  def _internal_replace_child(
      self,
      node: BNode,
      index: int,
      children: List[BNode],
  ) -> BNode:
    assert node.type == NodeType.INTERNAL
    new = BNode(node.type)
    for i in range(index):
      new.insert_data(i, node.get(i).key, node.get(i).value)
      new.set_child(i, node.get_child(i))
    for i, child in enumerate(children):
      new.insert_data(index + i, child.get(0).key, b"")
      new.set_child(index + i, self._new(child))
    for i in range(index + 1, node.nkeys):
      new.insert_data(i + len(children) - 1, node.get(i).key, node.get(i).value)
      new.set_child(i + len(children) - 1, node.get_child(i))
    return new

  def _internal_node_insert(
      self,
      node: BNode,
      idx: int,
      req: InsertReq,
  ) -> BNode:
    assert node.type == NodeType.INTERNAL
    child_id = node.get_child(idx)
    child = self._get(child_id)
    self._del(child_id)
    child = self._insert(child, req)
    splited = child.split3()
    return self._internal_replace_child(node, idx, splited)

  def _internal_node_delete(self, node: BNode, idx: int, req: DeleteReq):
    assert node.type == NodeType.INTERNAL
    child_id = node.get_child(idx)
    updated = self._delete(self._get(child_id), req)
    if updated.type == NodeType.NULL:
      return updated
    self._del(child_id)
    merge_dir, sibling = self._should_merge(node, idx, updated)
    if merge_dir == MergeDir.LEFT:
      merged = sibling.merge(updated)
      self._del(node.get_child(idx - 1))
      return node.replace2kid(idx - 1, self._new(merged), merged.get(0).key)
    if merge_dir == MergeDir.RIGHT:
      merged = updated.merge(sibling)
      self._del(node.get_child(idx + 1))
      return node.replace2kid(idx, self._new(merged), merged.get(0).key)
    assert updated.nkeys > 0
    return self._internal_replace_child(node, idx, [updated])

  def _insert(self, node: BNode, req: InsertReq) -> BNode:
    idx = node.lookup_le(req.key)
    if node.type == NodeType.LEAF:
      if req.key == node.get(idx).key:
        if req.mode == UpdateMode.INSERT_ONLY:
          raise ValueError("Can not insert to existed data")
        req.old = node.get(idx).value
        req.added, req.updated = False, True
        return node.leaf_update(idx, req.key, req.value)
      if req.mode == UpdateMode.UPDATE_ONLY:
        raise ValueError("Can not find the data to update")
      req.old = b""
      req.added, req.updated = True, True
      return node.leaf_insert(idx + 1, req.key, req.value)
    if node.type == NodeType.INTERNAL:
      return self._internal_node_insert(node, idx, req)
    raise ValueError("Invalid node type")

  def _delete(self, node: BNode, req: DeleteReq) -> BNode:
    idx = node.lookup_le(req.key)
    if node.type == NodeType.LEAF:
      if req.key != node.get(idx).key:
        req.old = b""
        req.deleted = False
        return BNode(NodeType.NULL)
      req.old = node.get(idx).value
      req.deleted = True
      return node.leaf_delete(idx)
    if node.type == NodeType.INTERNAL:
      return self._internal_node_delete(node, idx, req)
    raise ValueError("Invalid node type")

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def set_callbacks(
      self,
      new: Callable[[BNode,], int],
      get: Callable[[int,], BNode],
      delete: Callable[[int,], None],
  ):
    self._new = new
    self._get = get
    self._del = delete

  def delete(self, req: DeleteReq) -> bool:
    assert len(req.key) != 0
    assert len(req.key) <= MAX_KEY_SIZE
    if self.root == 0:
      return False

    updated = self._delete(self._get(self.root), req)
    if updated.type == NodeType.NULL:
      return False
    self._del(self.root)
    if updated.type == NodeType.INTERNAL and updated.nkeys == 1:
      self.root = updated.get_child(0)
    else:
      self.root = self._new(updated)
    return True

  def insert(self, req: InsertReq):
    assert len(req.key) != 0
    assert len(req.key) <= MAX_KEY_SIZE
    assert len(req.value) <= MAX_VALUE_SIZE
    if self.root == 0:
      if req.mode == UpdateMode.UPDATE_ONLY:
        raise ValueError("Can not update empty tree")
      root = BNode(NodeType.LEAF)
      root.insert_data(0, b"", b"")
      root.insert_data(1, req.key, req.value)
      self.root = self._new(root)
      req.old = b""
      req.added, req.updated = True, True
      return
    node = self._get(self.root)
    self._del(self.root)
    node = self._insert(node, req)
    splitted = node.split3()
    if len(splitted) > 1:
      root = BNode(NodeType.INTERNAL)
      for i, node in enumerate(splitted):
        child, key = self._new(node), node.get(0).key
        root.insert_data(i, key, b"")
        root.set_child(i, child)
      self.root = self._new(root)
    else:
      self.root = self._new(splitted[0])

  def get(self, key: bytes) -> bytes:
    assert len(key) != 0
    assert len(key) <= MAX_KEY_SIZE
    if self.root == 0:
      raise KeyError("Key not found")
    node = self._get(self.root)
    idx = node.lookup_le(key)
    if key == node.get(idx).key:
      return node.get(idx).value
    raise KeyError("Key not found")

  def render(self, filename: str):
    """
    Render the BTree to a file using graphviz.
    """
    dot = graphviz.Digraph()
    self._add_node(self._get(self.root), self.root, dot)
    dot.render(filename, format="png", view=True)
