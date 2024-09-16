from typing import Callable, List, Tuple, Optional
import copy
import graphviz

from database.btree.bnode import BNode
from database.btree.bnode import LeafNode
from database.btree.bnode import InternalNode
from database.constants import PAGE_SIZE
from database.constants import MAX_KEY_SZ
from database.constants import MAX_VALUE_SZ


class MergeDirection:
  NONE = 0
  LEFT = 1
  RIGHT = 2


class BTree:
  def __init__(
      self,
      *,
      get_: Callable[[int], BNode] = None,
      new_: Callable[[BNode], int] = None,
      del_: Callable[[int], None] = None,
      root: int = 0,
  ):
    self.root = root
    # Callbacks
    self._get = get_
    self._new = new_
    self._del = del_

  # ========================================================================= #
  # Internal API                                                              #
  # ========================================================================= #

  # ------------------------------------------------------------------------- #
  # Rendering                                                                 #
  # ------------------------------------------------------------------------- #

  def _add_node(self, node: BNode, dot: graphviz.Digraph):
    if isinstance(node, LeafNode):
      self._add_leaf(node, dot)
    if isinstance(node, InternalNode):
      self._add_internal(node, dot)

  def _add_leaf(self, node: LeafNode, dot: graphviz.Digraph):
    value_str = "\n".join([str(x[:5]) for x in node.keys])
    dot.node(str(id(node)), label=f"Leaf: {node.n_bytes}\n{value_str}")

  def _add_internal(self, node: InternalNode, dot: graphviz.Digraph):
    value_str = "\n".join([str(x[:5]) for x in node.keys])
    dot.node(str(id(node)), label=f"Internal: {node.n_bytes}\n{value_str}")
    for child in node.children:
      child = self._get(child)
      self._add_node(child, dot)
      dot.edge(str(id(node)), str(id(child)))

  # ------------------------------------------------------------------------- #
  # Insertion                                                                 #
  # ------------------------------------------------------------------------- #

  def _insert(self, node: BNode, key: bytes, value: bytes) -> BNode:
    idx = node.lookup_le(key)
    if isinstance(node, LeafNode):
      if node.keys[idx] == key:
        return self._update_leaf(node, idx, value)
      return self._insert_leaf(node, idx + 1, key, value)
    if isinstance(node, InternalNode):
      return self._insert_internal(node, idx, key, value)
    raise ValueError(f"Invalid node type: {node.type}")

  def _insert_leaf(
      self, node: LeafNode, idx: int, key: bytes, value: bytes
  ) -> LeafNode:
    new = copy.deepcopy(node)
    new.keys.insert(idx, key)
    new.values.insert(idx, value)
    return new

  def _update_leaf(
      self, node: LeafNode, idx: int, value: bytes
  ) -> LeafNode:
    new = copy.deepcopy(node)
    new.values[idx] = value
    return new

  def _insert_internal(
      self, node: InternalNode, idx: int, key: bytes, value: bytes
  ) -> InternalNode:
    child = self._get(node.children[idx])
    self._del(node.children[idx])
    new = self._insert(child, key, value)
    if new.n_bytes > PAGE_SIZE:
      children = self._split(new)
      return self._replace_child(node, idx, children)
    return self._replace_child(node, idx, [new])

  def _split(self, node: BNode) -> List[BNode]:
    if isinstance(node, LeafNode):
      return self._split_leaf(node)
    if isinstance(node, InternalNode):
      return self._split_internal(node)
    raise ValueError(f"Invalid node type: {node.type}")

  def _split_leaf(self, node: LeafNode) -> List[LeafNode]:
    mid = (node.n_keys + 1) // 2
    left = LeafNode(node.type, node.keys[:mid], node.values[:mid])
    right = LeafNode(node.type, node.keys[mid:], node.values[mid:])
    if left.n_bytes > PAGE_SIZE:
      return [*self._split_leaf(left), right]
    if right.n_bytes > PAGE_SIZE:
      return [left, *self._split_leaf(right)]
    return [left, right]

  def _split_internal(
      self, node: InternalNode
  ) -> List[InternalNode]:
    mid = (node.n_keys + 1) // 2
    left = InternalNode(
        node.type, node.keys[:mid], node.children[:mid]
    )
    right = InternalNode(
        node.type, node.keys[mid:], node.children[mid:]
    )
    if left.n_bytes > PAGE_SIZE:
      return [*self._split_internal(left), right]
    if right.n_bytes > PAGE_SIZE:
      return [left, *self._split_internal(right)]
    return [left, right]

  def _replace_child(
      self, node: InternalNode, idx: int, nodes: List[BNode]
  ) -> InternalNode:
    new = copy.deepcopy(node)
    new.keys.pop(idx)
    new.children.pop(idx)
    for i, child in enumerate(nodes):
      new.keys.insert(idx + i, child.keys[0])
      new.children.insert(idx + i, self._new(child))
    return new

  # ------------------------------------------------------------------------- #
  # Deletion                                                                  #
  # ------------------------------------------------------------------------- #

  def _delete(self, node: BNode, key: bytes) -> BNode:
    idx = node.lookup_le(key)
    if isinstance(node, LeafNode):
      return self._delete_leaf(node, idx)
    if isinstance(node, InternalNode):
      return self._delete_internal(node, idx, key)
    raise ValueError(f"Invalid node type: {node.type}")

  def _delete_leaf(self, node: LeafNode, idx: int) -> LeafNode:
    new = copy.deepcopy(node)
    new.keys.pop(idx)
    new.values.pop(idx)
    return new

  def _delete_internal(
      self, node: InternalNode, idx: int, key: bytes
  ) -> InternalNode:
    child = self._get(node.children[idx])
    child = self._delete(child, key)
    # PAGE_SIZE // 4 is a heuristic to determine if we should merge
    if child.n_bytes < PAGE_SIZE // 4:
      merge_dir, sibling = self._should_merge(node, child, idx)
      if merge_dir == MergeDirection.LEFT:
        new = self._merge(sibling, child)
        return self._replace2child(node, idx - 1, new)
      if merge_dir == MergeDirection.RIGHT:
        new = self._merge(child, sibling)
        return self._replace2child(node, idx, new)
    return self._replace_child(node, idx, [child])

  def _should_merge(
      self, node: InternalNode, child: BNode, idx: int
  ) -> Tuple[MergeDirection, BNode]:
    # -6 mean the header size of a child node
    if idx > 0:
      left = self._get(node.children[idx - 1])
      if left.n_bytes + child.n_bytes - 6 < PAGE_SIZE:
        return MergeDirection.LEFT, left
    if idx < node.n_keys - 1:
      right = self._get(node.children[idx + 1])
      if right.n_bytes + child.n_bytes - 6 < PAGE_SIZE:
        return MergeDirection.RIGHT, right
    return MergeDirection.NONE, child

  def _merge(
      self, left: BNode, right: BNode
  ) -> BNode:
    assert left.type == right.type
    if isinstance(left, LeafNode):
      return self._merge_leaf(left, right)
    if isinstance(left, InternalNode):
      return self._merge_internal(left, right)
    raise ValueError(f"Invalid node type: {left.type}")

  def _merge_leaf(
      self, left: LeafNode, right: LeafNode
  ) -> LeafNode:
    new = copy.deepcopy(left)
    new.keys.extend(right.keys)
    new.values.extend(right.values)
    return new

  def _merge_internal(
      self, left: InternalNode, right: InternalNode
  ) -> InternalNode:
    new = copy.deepcopy(left)
    new.keys.extend(right.keys)
    new.children.extend(right.children)
    return new

  def _replace2child(
      self, node: InternalNode, idx: int, new: BNode
  ) -> InternalNode:
    new_node = copy.deepcopy(node)
    new_node.keys = new_node.keys[:idx] + new_node.keys[idx + 1:]
    new_node.children = new_node.children[:idx] + new_node.children[idx + 1:]
    self._del(node.children[idx])
    self._del(node.children[idx + 1])
    new_node.keys[idx] = new.keys[0]
    new_node.children[idx] = self._new(new)
    return new_node

  # ------------------------------------------------------------------------- #
  # Lookup                                                                    #
  # ------------------------------------------------------------------------- #

  def _lookup(self, node: BNode, key: bytes) -> Optional[bytes]:
    idx = node.lookup_le(key)
    if isinstance(node, LeafNode):
      if node.keys[idx] == key:
        return node.values[idx]
      return None
    if isinstance(node, InternalNode):
      child = self._get(node.children[idx])
      return self._lookup(child, key)
    raise ValueError(f"Invalid node type: {node.type}")

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def insert(self, key: bytes, value: bytes) -> None:
    assert 0 < len(key) <= MAX_KEY_SZ
    assert len(value) <= MAX_VALUE_SZ
    if self.root == 0:
      leaf = LeafNode(keys=[], values=[])
      leaf.keys.append(b"")
      leaf.values.append(b"")
      leaf.keys.append(key)
      leaf.values.append(value)
      self.root = self._new(leaf)
      return
    root = self._get(self.root)
    self._del(self.root)
    root = self._insert(root, key, value)
    if root.n_bytes > PAGE_SIZE:
      children = self._split(root)
      root = InternalNode(
          type=InternalNode.type,
          keys=[x.keys[0] for x in children],
          children=[self._new(x) for x in children],
      )
    self.root = self._new(root)

  def delete(self, key: bytes) -> None:
    assert 0 < len(key) <= MAX_KEY_SZ
    if self.root == 0:
      raise ValueError("Key not found")
    root = self._get(self.root)
    self._del(self.root)
    root = self._delete(root, key)
    if isinstance(root, InternalNode) and root.n_keys == 1:
      self.root = root.children[0]
      return
    self.root = self._new(root)

  def get(self, key: bytes) -> Optional[bytes]:
    assert 0 < len(key) <= MAX_KEY_SZ
    if self.root == 0:
      return None
    root = self._get(self.root)
    return self._lookup(root, key)

  def get_node_by_id(self, idx: int) -> BNode:
    return self._get(idx)

  def render(self, filename="btree.gv") -> None:
    dot = graphviz.Digraph()
    root = self._get(self.root)
    self._add_node(root, dot)
    dot.render(filename, format="png", cleanup=True, view=True)
