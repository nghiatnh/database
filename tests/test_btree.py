from database.btree.bnode import InternalNode
from database.btree import BNode
from database.btree import BTree


class CustomTree:
  def __init__(self):
    self.tree = BTree(get_=self.get_, new_=self.new_, del_=self.del_)
    self.n = 0
    self.ref = {}

  def new_(self, node: BNode) -> int:
    self.n += 1
    self.ref[self.n] = node
    return self.n

  def get_(self, idx: int) -> BNode:
    return self.ref[idx]

  def del_(self, idx: int):
    del self.ref[idx]


def test_insert_leaf():
  tree = CustomTree()
  tree.tree.insert(b"1", b"one")
  tree.tree.insert(b"2", b"two")
  tree.tree.insert(b"3", b"three")
  assert tree.tree.root == 3
  assert tree.tree.get(b"1") == b"one"
  assert tree.tree.get(b"2") == b"two"
  assert tree.tree.get(b"3") == b"three"


def test_insert_internal():
  tree = CustomTree()
  tree.tree.insert(b"1" * 200, b"one" * 200)
  tree.tree.insert(b"3" * 200, b"three" * 200)
  tree.tree.insert(b"2" * 1000, b"two" * 1000)
  assert tree.tree.root == 6
  root_node = tree.tree.get_node_by_id(tree.tree.root)
  assert isinstance(root_node, InternalNode)
  assert root_node.children == [3, 4, 5]
  assert tree.tree.get(b"1" * 200) == b"one" * 200
  assert tree.tree.get(b"2" * 1000) == b"two" * 1000
  assert tree.tree.get(b"3" * 200) == b"three" * 200


def test_delete_leaf():
  tree = CustomTree()
  tree.tree.insert(b"1", b"one")
  tree.tree.insert(b"2", b"two")
  tree.tree.insert(b"3", b"three")
  tree.tree.delete(b"2")
  assert tree.tree.root == 4
  assert tree.tree.get(b"1") == b"one"
  assert tree.tree.get(b"2") is None
  assert tree.tree.get(b"3") == b"three"


def test_delete_internal():
  tree = CustomTree()
  tree.tree.insert(b"1" * 200, b"one" * 200)
  tree.tree.insert(b"3" * 200, b"three" * 100)
  tree.tree.insert(b"2" * 1000, b"two" * 1000)
  tree.tree.delete(b"2" * 1000)
  tree.tree.render()
  assert tree.tree.root == 8
  root_node = tree.tree.get_node_by_id(tree.tree.root)
  assert isinstance(root_node, InternalNode)
  assert root_node.children == [7, 5]
  assert tree.tree.get(b"1" * 200) == b"one" * 200
  assert tree.tree.get(b"2" * 1000) is None
  assert tree.tree.get(b"3" * 200) == b"three" * 100
