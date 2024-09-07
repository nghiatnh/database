from typing import Callable, List, Tuple
import graphviz

from database.btree.node import Node
from database.btree.constants import NodeType
from database.btree.constants import MergeDir
from database.btree.constants import PAGE_SIZE
from database.btree.constants import MAX_KEY_SIZE
from database.btree.constants import MAX_VALUE_SIZE


class BTree:
  def __init__(self):
    self._root: int = 0
    # Callbacks
    self._get: Callable[[int,], Node]
    self._new: Callable[[Node,], int]
    self._del: Callable[[int,], None]

  def _add_node(self, node: Node, idx: int, dot: graphviz.Digraph):
    dot.node(str(id(node)), f"{idx} ({node.type.name}): {node.get(0).key[:5]}")
    for i in range(node.nkeys):
      child = node.get_child(i)
      if child != 0:
        self._add_node(self._get(child), child, dot)
        dot.edge(str(id(node)), str(id(self._get(child))))

  def _should_merge(
      self,
      node: Node,
      index: int,
      updated: Node,
  ) -> Tuple[MergeDir, Node]:
    if updated.total_bytes > PAGE_SIZE / 4:
      return MergeDir.NONE, Node(NodeType.NULL)
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
    return MergeDir.NONE, Node(NodeType.NULL)

  def _internal_replace_child(
      self,
      node: Node,
      index: int,
      children: List[Node],
  ) -> Node:
    assert node.type == NodeType.INTERNAL
    new = Node(node.type)
    for i in range(index):
      new.insert_data(i, node.get(i).key, node.get(i).value)
      new.set_child(i, node.get_child(i))
    for i, child in enumerate(children):
      new.insert_data(index + i, child.get(0).key, b'')
      new.set_child(index + i, self._new(child))
    for i in range(index + 1, node.nkeys):
      new.insert_data(i + len(children), node.get(i).key, node.get(i).value)
      new.set_child(i + len(children), node.get_child(i))
    return new

  def _internal_node_insert(
          self, node: Node, idx: int, key: bytes, value: bytes) -> Node:
    assert node.type == NodeType.INTERNAL
    child_id = node.get_child(idx)
    child = self._get(child_id)
    self._del(child_id)
    child = self._insert(child, key, value)
    splited = child.split3()
    return self._internal_replace_child(node, idx, splited)

  def _internal_node_delete(self, node: Node, idx: int, key: bytes):
    assert node.type == NodeType.INTERNAL
    child_id = node.get_child(idx)
    updated = self._delete(self._get(child_id), key)
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

  def _insert(self, node: Node, key: bytes, value: bytes) -> Node:
    idx = node.lookup_le(key)
    if node.type == NodeType.LEAF:
      if key == node.get(idx).key:
        return node.leaf_update(idx, key, value)
      return node.leaf_insert(idx + 1, key, value)
    if node.type == NodeType.INTERNAL:
      return self._internal_node_insert(node, idx, key, value)
    raise ValueError("Invalid node type")

  def _delete(self, node: Node, key: bytes) -> Node:
    idx = node.lookup_le(key)
    if node.type == NodeType.LEAF:
      if key != node.get(idx).key:
        return Node(NodeType.NULL)
      return node.leaf_delete(idx)
    if node.type == NodeType.INTERNAL:
      return self._internal_node_delete(node, idx, key)
    raise ValueError("Invalid node type")

  def set_callbacks(
      self,
      new: Callable[[Node,], int],
      get: Callable[[int,], Node],
      delete: Callable[[int,], None],
  ):
    self._new = new
    self._get = get
    self._del = delete

  def delete(self, key: bytes) -> bool:
    assert len(key) != 0
    assert len(key) <= MAX_KEY_SIZE
    if self._root == 0:
      return False

    updated = self._delete(self._get(self._root), key)
    if updated.type == NodeType.NULL:
      return False
    self._del(self._root)
    if updated.type == NodeType.INTERNAL and updated.nkeys == 1:
      self._root = updated.get_child(0)
    else:
      self._root = self._new(updated)
    return True

  def insert(self, key: bytes, value: bytes):
    assert len(key) != 0
    assert len(key) <= MAX_KEY_SIZE
    assert len(value) <= MAX_VALUE_SIZE
    if self._root == 0:
      root = Node(NodeType.LEAF)
      root.insert_data(0, b'', b'')
      root.insert_data(1, key, value)
      self._root = self._new(root)
      return
    node = self._get(self._root)
    self._del(self._root)
    node = self._insert(node, key, value)
    splitted = node.split3()
    if len(splitted) > 1:
      root = Node(NodeType.INTERNAL)
      for i, node in enumerate(splitted):
        child, key = self._new(node), node.get(0).key
        root.insert_data(i, key, b'')
        root.set_child(i, child)
      self._root = self._new(root)
    else:
      self._root = self._new(splitted[0])

  def get(self, key: bytes) -> bytes:
    assert len(key) != 0
    assert len(key) <= MAX_KEY_SIZE
    if self._root == 0:
      raise KeyError("Key not found")
    node = self._get(self._root)
    idx = node.lookup_le(key)
    if key == node.get(idx).key:
      return node.get(idx).value
    raise KeyError("Key not found")

  def render_tree(self, filename: str):
    """
    Render the abstract syntax tree to a file using graphviz.
    """
    dot = graphviz.Digraph()
    self._add_node(self._get(self._root), self._root, dot)
    dot.render(filename, format="png", view=True)
