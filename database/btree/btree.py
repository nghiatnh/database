from typing import Callable, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import copy
import graphviz

from database.btree.bnode import BNode
from database.btree.bnode import LeafNode
from database.btree.bnode import InternalNode
from database.constants import SetMode
from database.constants import PAGE_SIZE
from database.constants import MAX_KEY_SZ
from database.constants import MAX_VALUE_SZ


class MergeDirection(Enum):
  NONE = 0
  LEFT = 1
  RIGHT = 2


@dataclass
class SetRequest:
  """
  SetRequest
  ==========
  SetRequest class represents a request to set a key-value pair in the BTree.
  """

  key: bytes
  value: bytes
  mode: SetMode = SetMode.UPSERT

  def check(self):
    """
    Check the validity of the request.
    """
    assert 0 < len(self.key) <= MAX_KEY_SZ
    assert len(self.value) <= MAX_VALUE_SZ


@dataclass
class SetResponse:
  """
  SetResponse
  ===========
  SetResponse class represents a response to a set request. It contains
  information about the success or failure of the request.
  """

  added: bool = False
  updated: bool = False
  old_value: bytes = b""
  message: str = ""

  def update_ok(self):
    """
    Set the response to indicate that the update was successful.
    """
    self.added = False
    self.updated = True

  def add_ok(self):
    """
    Set the response to indicate that the addition was successful
    """
    self.added = True
    self.updated = True

  def set_fail(self, msg: str = ""):
    """
    Set the response to indicate that the set operation failed.
    """
    self.added = False
    self.updated = False
    self.message = msg


@dataclass
class DeleteRequest:
  """
  DeleteRequest
  =============
  DeleteRequest class represents a request to delete a key from the BTree.
  """

  key: bytes

  def check(self):
    """
    Check the validity of the request.
    """
    assert 0 < len(self.key) <= MAX_KEY_SZ


@dataclass
class DeleteResponse:
  """
  DeleteResponse
  ==============
  DeleteResponse class represents a response to a delete request. It contains
  information about the success or failure of the request.
  """

  deleted: bool = False
  message: str = ""

  def delete_ok(self):
    """
    Set the response to indicate that the deletion was successful.
    """
    self.deleted = True

  def delete_fail(self, msg: str = ""):
    """
    Set the response to indicate that the deletion failed.
    """
    self.deleted = False
    self.message = msg


class BTree:
  """
  BTree
  =====
  BTree class represents a BTree data structure. It provides methods to set,
  get, and delete key-value pairs in the BTree.
  """

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

  def _add_node(self, node: BNode, idx: int, dot: graphviz.Digraph):
    if isinstance(node, LeafNode):
      self._add_leaf(node, idx, dot)
    if isinstance(node, InternalNode):
      self._add_internal(node, idx, dot)

  def _add_leaf(self, node: LeafNode, idx: int, dot: graphviz.Digraph):
    value_str = "\n".join([str(x[:5]) for x in node.keys])
    dot.node(str(idx), label=f"Leaf: {node.n_bytes}\n{value_str}")

  def _add_internal(self, node: InternalNode, idx: int, dot: graphviz.Digraph):
    value_str = "\n".join([str(x[:5]) for x in node.keys])
    dot.node(str(idx), label=f"Internal: {node.n_bytes}\n{value_str}")
    for child_id in node.children:
      child = self._get(child_id)
      self._add_node(child, child_id, dot)
      dot.edge(str(idx), str(child_id))

  # ------------------------------------------------------------------------- #
  # Insertion                                                                 #
  # ------------------------------------------------------------------------- #

  def _set(self, node: BNode, req: SetRequest, res: SetResponse) -> BNode:
    idx = node.lookup_le(req.key)
    if isinstance(node, LeafNode):
      if node.keys[idx] == req.key:
        if req.mode == SetMode.INSERT_ONLY:
          res.set_fail("Key already exists")
          return node
        res.update_ok()
        res.old_value = node.values[idx]
        return self._update_leaf(node, idx, req)
      if req.mode == SetMode.UPDATE_ONLY:
        res.set_fail("Key not found")
        return node
      res.add_ok()
      return self._insert_leaf(node, idx + 1, req)
    if isinstance(node, InternalNode):
      return self._set_internal(node, idx, req, res)
    raise ValueError(f"Invalid node type: {node.type}")

  def _insert_leaf(
      self, node: LeafNode, idx: int, req: SetRequest
  ) -> LeafNode:
    new = copy.deepcopy(node)
    new.keys.insert(idx, req.key)
    new.values.insert(idx, req.value)
    return new

  def _update_leaf(
      self, node: LeafNode, idx: int, req: SetRequest
  ) -> LeafNode:
    new = copy.deepcopy(node)
    new.values[idx] = req.value
    return new

  def _set_internal(
      self, node: InternalNode, idx: int, req: SetRequest, res: SetResponse
  ) -> InternalNode:
    child = self._get(node.children[idx])
    self._del(node.children[idx])
    new = self._set(child, req, res)
    if not res.updated:
      return node
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

  def _delete(
      self,
      node: BNode,
      req: DeleteRequest,
      res: DeleteResponse,
  ) -> BNode:
    idx = node.lookup_le(req.key)
    if isinstance(node, LeafNode):
      if node.keys[idx] != req.key:
        res.delete_fail("Key not found")
        return node
      res.delete_ok()
      return self._delete_leaf(node, idx)
    if isinstance(node, InternalNode):
      return self._delete_internal(node, idx, req, res)
    raise ValueError(f"Invalid node type: {node.type}")

  def _delete_leaf(self, node: LeafNode, idx: int) -> LeafNode:
    new = copy.deepcopy(node)
    new.keys.pop(idx)
    new.values.pop(idx)
    return new

  def _delete_internal(
      self,
      node: InternalNode,
      idx: int,
      req: DeleteRequest,
      res: DeleteResponse
  ) -> InternalNode:
    child = self._get(node.children[idx])
    child = self._delete(child, req, res)
    if not res.deleted:
      return node
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

  def set(self, req: SetRequest) -> SetResponse:
    """
    Set a key-value pair in the BTree.
    """
    req.check()
    res = SetResponse()
    if self.root == 0:
      leaf = LeafNode(keys=[], values=[])
      leaf.keys.append(b"")
      leaf.values.append(b"")
      leaf.keys.append(req.key)
      leaf.values.append(req.value)
      self.root = self._new(leaf)
      res.add_ok()
      return res
    root = self._get(self.root)
    self._del(self.root)
    root = self._set(root, req, res)
    if not res.updated:
      return res
    if root.n_bytes > PAGE_SIZE:
      children = self._split(root)
      root = InternalNode(
          type=InternalNode.type,
          keys=[x.keys[0] for x in children],
          children=[self._new(x) for x in children],
      )
    self.root = self._new(root)
    return res

  def delete(self, req: DeleteRequest) -> DeleteResponse:
    """
    Delete a key-value pair from the BTree.
    """
    req.check()
    res = DeleteResponse()
    if self.root == 0:
      res.delete_fail("Key not found")
      return res
    root = self._get(self.root)
    self._del(self.root)
    root = self._delete(root, req, res)
    if not res.deleted:
      return res
    if isinstance(root, InternalNode) and root.n_keys == 1:
      self.root = root.children[0]
      return res
    self.root = self._new(root)
    return res

  def get(self, key: bytes) -> Optional[bytes]:
    """
    Get the value associated with a key.
    """
    assert 0 < len(key) <= MAX_KEY_SZ
    if self.root == 0:
      return None
    root = self._get(self.root)
    return self._lookup(root, key)

  def get_node_by_id(self, idx: int) -> BNode:
    """
    Get a node by its index.
    """
    return self._get(idx)

  def render(self, filename="btree.gv") -> None:
    """
    Render the BTree to a file.
    """
    dot = graphviz.Digraph()
    root = self._get(self.root)
    self._add_node(root, self.root, dot)
    dot.render(filename, format="png", cleanup=True, view=True)
