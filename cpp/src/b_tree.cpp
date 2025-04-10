#include "b_tree.h"

#include <iostream>

#include "b_node.h"
#include "constants.h"
#include "debug.h"

using namespace std;

namespace cpp_database {

// Insert a key-value pair
void BTree::insert(const ByteArray& key, const ByteArray& value) {
  if (is_empty()) {
    ByteArray arr{PAGE_SIZE};
    arr.set_value<byte>(0, static_cast<byte>(NodeType::LEAF));
    arr.set_value<size_t>(1, 0);
    root = store_driver->new_page(arr);
  }
  auto root_page = get_node(store_driver->get(root));
  auto old_root = root;
  auto result = insert_node(*root_page, key, value);
  if (result->data_size() > PAGE_SIZE) {
    BInternalNode parent{ByteArray{PAGE_SIZE}};
    parent.set_type(NodeType::INTERNAL);
    parent.set_n_keys(0);
    auto new_node = split_node(parent, 0, *result).release();
    root = store_driver->new_page(new_node->data_arr().slice(0, PAGE_SIZE));
  } else {
    root = store_driver->new_page(result->data_arr().slice(0, PAGE_SIZE));
  }
  store_driver->delete_page(old_root);
}

// Insert Internal
unique_ptr<BNode> BTree::insert_node(const BNode& node, const ByteArray& key, const ByteArray& value) const {
  auto index = search_key(node, key);
  if (node.type() == NodeType::LEAF) {
    ByteArray arr{2 * PAGE_SIZE};
    arr.set_value(0, node.data_arr());
    BLeafNode leaf{arr};
    return make_unique<BLeafNode>(leaf.insert_key(index, key, value));
  }
  auto internal = static_cast<const BInternalNode&>(node);
  auto page = internal.get_pointer(index);
  auto page_node = get_node(store_driver->get(page));
  auto result = insert_node(*page_node, key, value);
  if (result->data_size() > PAGE_SIZE) {
    auto new_node = split_node(internal, index, *result);
    store_driver->delete_page(page);
    return new_node;
  }
  auto result_page = store_driver->new_page(result->data_arr().slice(0, PAGE_SIZE));
  internal.set_pointer(index, result_page);
  store_driver->delete_page(page);
  return make_unique<BInternalNode>(internal);
}

unique_ptr<BInternalNode> BTree::split_node(const BInternalNode& parent, size_t index, const BLeafNode& node) const {
  size_t n_left = (node.n_keys() + 1) / 2;
  size_t n_right = node.n_keys() - n_left;

  BLeafNode left{ByteArray{PAGE_SIZE}};
  BLeafNode right{ByteArray{PAGE_SIZE}};
  left.set_type(NodeType::LEAF);
  right.set_type(NodeType::LEAF);
  left.set_n_keys(n_left);
  right.set_n_keys(n_right);
  for (size_t i = 0; i < n_left + 1; ++i) {
    left.set_offset(i, node.get_offset(i));
  }
  for (size_t i = n_left; i < node.n_keys() + 1; ++i) {
    right.set_offset(i - n_left, node.get_offset(i) - node.get_offset(n_left));
  }
  for (size_t i = 0; i < n_left; ++i) {
    left.set_key_value(i, node.get_key(i), node.get_value(i));
  }
  for (size_t i = n_left; i < node.n_keys(); ++i) {
    right.set_key_value(i - n_left, node.get_key(i), node.get_value(i));
  }
  auto left_ptr = store_driver->new_page(left.data_arr());
  auto right_ptr = store_driver->new_page(right.data_arr());

  BInternalNode new_parent{ByteArray{2 * PAGE_SIZE}};
  new_parent.set_type(NodeType::INTERNAL);
  new_parent.set_n_keys(parent.n_keys() + 1);
  for (size_t i = 0; i < index; ++i) {
    new_parent.set_pointer(i, parent.get_pointer(i));
  }
  new_parent.set_pointer(index, left_ptr);
  new_parent.set_pointer(index + 1, right_ptr);
  for (size_t i = index + 2; i < new_parent.n_keys() + 1; ++i) {
    new_parent.set_pointer(i, parent.get_pointer(i - 1));
  }
  for (size_t i = 0; i <= index; ++i) {
    new_parent.set_offset(i, parent.get_offset(i));
  }
  for (size_t i = index + 1; i < new_parent.n_keys() + 1; ++i) {
    new_parent.set_offset(i, parent.get_offset(i - 1) + node.get_key(n_left).size());
  }
  for (size_t i = 0; i < index; ++i) {
    new_parent.set_key(i, parent.get_key(i));
  }
  new_parent.set_key(index, node.get_key(n_left));
  for (size_t i = index + 1; i < new_parent.n_keys(); ++i) {
    new_parent.set_key(i, parent.get_key(i - 1));
  }
  return make_unique<BInternalNode>(new_parent);
}

// Split leaf node
unique_ptr<BInternalNode> BTree::split_node(const BInternalNode& parent, size_t index,
                                            const BInternalNode& node) const {
  auto n_left = (node.n_keys() + 1) / 2;
  auto n_right = node.n_keys() - n_left;
  n_left -= 1;

  BInternalNode left{ByteArray{PAGE_SIZE}};
  BInternalNode right{ByteArray{PAGE_SIZE}};
  left.set_type(NodeType::INTERNAL);
  right.set_type(NodeType::INTERNAL);
  left.set_n_keys(n_left);
  right.set_n_keys(n_right);
  for (size_t i = 0; i < n_left + 1; ++i) {
    left.set_offset(i, node.get_offset(i));
  }
  for (size_t i = n_left + 1; i < node.n_keys() + 1; ++i) {
    right.set_offset(i - n_left - 1, node.get_offset(i) - node.get_offset(n_left + 1));
  }
  for (size_t i = 0; i < n_left + 1; ++i) {
    left.set_pointer(i, node.get_pointer(i));
  }
  for (size_t i = n_left + 1; i < node.n_keys() + 1; ++i) {
    right.set_pointer(i - n_left - 1, node.get_pointer(i));
  }
  for (size_t i = 0; i < n_left; ++i) {
    left.set_key(i, node.get_key(i));
  }
  for (size_t i = n_left + 1; i < node.n_keys(); ++i) {
    right.set_key(i - n_left - 1, node.get_key(i));
  }
  auto left_ptr = store_driver->new_page(left.data_arr());
  auto right_ptr = store_driver->new_page(right.data_arr());

  BInternalNode new_parent{ByteArray{2 * PAGE_SIZE}};
  new_parent.set_type(NodeType::INTERNAL);
  new_parent.set_n_keys(parent.n_keys() + 1);
  for (size_t i = 0; i < index; ++i) {
    new_parent.set_pointer(i, parent.get_pointer(i));
  }
  new_parent.set_pointer(index, left_ptr);
  new_parent.set_pointer(index + 1, right_ptr);
  for (size_t i = index + 2; i < new_parent.n_keys() + 1; ++i) {
    new_parent.set_pointer(i, parent.get_pointer(i - 1));
  }
  for (size_t i = 0; i <= index; ++i) {
    new_parent.set_offset(i, parent.get_offset(i));
  }
  for (size_t i = index + 1; i < new_parent.n_keys() + 1; ++i) {
    new_parent.set_offset(i, parent.get_offset(i - 1) + node.get_key(n_left).size());
  }
  for (size_t i = 0; i < index; ++i) {
    new_parent.set_key(i, parent.get_key(i));
  }
  new_parent.set_key(index, node.get_key(n_left));
  for (size_t i = index + 1; i < new_parent.n_keys(); ++i) {
    new_parent.set_key(i, parent.get_key(i - 1));
  }
  return make_unique<BInternalNode>(new_parent);
}

// Remove a key
void BTree::remove(const ByteArray& key) {
  auto root_page = get_node(store_driver->get(root));
  auto old_root = root;
  auto result = remove_node(*root_page, key);
  root = store_driver->new_page(result->data_arr().slice(0, PAGE_SIZE));
  store_driver->delete_page(old_root);
}

// Insert Internal
unique_ptr<BNode> BTree::remove_node(const BNode& node, const ByteArray& key) const {
  if (node.type() == NodeType::LEAF) {
    auto leaf = static_cast<const BLeafNode&>(node);
    auto index = search_exact_key(leaf, key);
    return make_unique<BLeafNode>(leaf.remove_key(index));
  }
  auto internal = static_cast<const BInternalNode&>(node);
  auto offset = search_key(internal, key);
  auto page = internal.get_pointer(offset);
  auto page_node = get_node(store_driver->get(page));
  auto result = remove_node(*page_node, key).release();
  if (result->data_size() < PAGE_SIZE / 2) {
    if (offset > 0) {
      auto left = get_node(store_driver->get(internal.get_pointer(offset - 1)));
      if (left->data_size() < PAGE_SIZE * 2 / 4 || result->n_keys() == 0) {
        auto new_node = merge_node(internal, offset - 1, *left, *result);
        store_driver->delete_page(page);
        return new_node;
      }
    }
    if (offset < internal.n_keys()) {
      auto right = get_node(store_driver->get(internal.get_pointer(offset + 1)));
      if (right->data_size() < PAGE_SIZE * 2 / 4 || result->n_keys() == 0) {
        auto new_node = merge_node(internal, offset, *result, *right);
        store_driver->delete_page(page);
        return new_node;
      }
    }
  }
  auto result_page = store_driver->new_page(result->data_arr().slice(0, PAGE_SIZE));
  internal.set_pointer(offset, result_page);
  store_driver->delete_page(page);
  return make_unique<BInternalNode>(internal);
}

// Split internal node
unique_ptr<BNode> BTree::merge_node(const BInternalNode& parent, size_t index, const BLeafNode& left,
                                    const BLeafNode& right) const {
  BLeafNode new_node{ByteArray{PAGE_SIZE}};
  new_node.set_type(NodeType::LEAF);
  new_node.set_n_keys(left.n_keys() + right.n_keys());
  for (size_t i = 0; i < left.n_keys(); ++i) {
    new_node.set_offset(i, left.get_offset(i));
  }
  for (size_t i = left.n_keys(); i < new_node.n_keys() + 1; ++i) {
    new_node.set_offset(i, right.get_offset(i - left.n_keys()) + left.get_offset(left.n_keys()));
  }
  for (size_t i = 0; i < left.n_keys(); ++i) {
    new_node.set_key_value(i, left.get_key(i), left.get_value(i));
  }
  for (size_t i = left.n_keys(); i < new_node.n_keys(); ++i) {
    new_node.set_key_value(i, right.get_key(i - left.n_keys()), right.get_value(i - left.n_keys()));
  }

  // For root node
  if (parent.n_keys() == 1) {
    return make_unique<BLeafNode>(new_node.data_arr());
  }

  auto new_ptr = store_driver->new_page(new_node.data_arr());

  BInternalNode new_parent{ByteArray{2 * PAGE_SIZE}};
  new_parent.set_type(NodeType::INTERNAL);
  new_parent.set_n_keys(parent.n_keys() - 1);
  for (size_t i = 0; i < index; ++i) {
    new_parent.set_pointer(i, parent.get_pointer(i));
  }
  new_parent.set_pointer(index, new_ptr);
  for (size_t i = index + 1; i < new_parent.n_keys() + 1; ++i) {
    new_parent.set_pointer(i, parent.get_pointer(i + 1));
  }
  for (size_t i = 0; i <= index; ++i) {
    new_parent.set_offset(i, parent.get_offset(i));
  }
  for (size_t i = index + 1; i < new_parent.n_keys() + 1; ++i) {
    new_parent.set_offset(i, parent.get_offset(i + 1) - parent.get_key(index).size());
  }
  for (size_t i = 0; i < index; ++i) {
    new_parent.set_key(i, parent.get_key(i));
  }
  for (size_t i = index; i < new_parent.n_keys(); ++i) {
    new_parent.set_key(i, parent.get_key(i + 1));
  }
  return make_unique<BInternalNode>(new_parent);
}

// Split leaf node
unique_ptr<BNode> BTree::merge_node(const BInternalNode& parent, size_t index, const BInternalNode& left,
                                    const BInternalNode& right) const {
  BInternalNode new_node{ByteArray{PAGE_SIZE}};
  new_node.set_type(NodeType::INTERNAL);
  new_node.set_n_keys(left.n_keys() + right.n_keys() + 1);
  auto add_page = get_node(store_driver->get(right.get_pointer(0)));
  size_t add_sz = add_page->get_key(0).size();

  for (size_t i = 0; i < left.n_keys() + 1; ++i) {
    new_node.set_offset(i, left.get_offset(i));
  }
  new_node.set_offset(left.n_keys() + 1, left.get_offset(left.n_keys()) + add_sz);
  for (size_t i = left.n_keys() + 2; i < new_node.n_keys() + 1; ++i) {
    new_node.set_offset(i, right.get_offset(i - left.n_keys() - 1) + left.get_offset(left.n_keys()) + add_sz);
  }
  for (size_t i = 0; i < left.n_keys() + 1; ++i) {
    new_node.set_pointer(i, left.get_pointer(i));
  }
  for (size_t i = left.n_keys() + 1; i < new_node.n_keys() + 1; ++i) {
    new_node.set_pointer(i, right.get_pointer(i - left.n_keys() - 1));
  }
  for (size_t i = 0; i < left.n_keys(); ++i) {
    new_node.set_key(i, left.get_key(i));
  }
  for (size_t i = left.n_keys() + 1; i < new_node.n_keys(); ++i) {
    new_node.set_key(i, right.get_key(i - left.n_keys() - 1));
  }
  new_node.set_key(left.n_keys(), add_page->get_key(0));

  // For root only
  if (parent.n_keys() == 1) {
    return make_unique<BInternalNode>(new_node);
  }

  auto new_ptr = store_driver->new_page(new_node.data_arr());

  BInternalNode new_parent{ByteArray{2 * PAGE_SIZE}};
  new_parent.set_type(NodeType::INTERNAL);
  new_parent.set_n_keys(parent.n_keys() - 1);
  for (size_t i = 0; i < index; ++i) {
    new_parent.set_pointer(i, parent.get_pointer(i));
  }
  new_parent.set_pointer(index, new_ptr);
  for (size_t i = index + 1; i < new_parent.n_keys() + 1; ++i) {
    new_parent.set_pointer(i, parent.get_pointer(i + 1));
  }
  for (size_t i = 0; i <= index; ++i) {
    new_parent.set_offset(i, parent.get_offset(i));
  }
  for (size_t i = index + 1; i < new_parent.n_keys() + 1; ++i) {
    new_parent.set_offset(i, parent.get_offset(i + 1) - parent.get_key(index).size());
  }
  for (size_t i = 0; i < index; ++i) {
    new_parent.set_key(i, parent.get_key(i));
  }
  for (size_t i = index; i < new_parent.n_keys(); ++i) {
    new_parent.set_key(i, parent.get_key(i + 1));
  }
  return make_unique<BInternalNode>(new_parent);
}

// Search key
size_t BTree::search_key(const BNode& node, const ByteArray& key) const {
  if (node.n_keys() == 0) return 0;
  size_t i = 0;
  while (i < node.n_keys() && key >= node.get_key(i)) {
    ++i;
  }
  return i;
};

// Search key
int BTree::search_exact_key(const BLeafNode& node, const ByteArray& key) const {
  if (node.n_keys() == 0) return -1;
  for (size_t i = 0; i < node.n_keys(); ++i) {
    if (node.get_key(i) == key) {
      return i;
    }
  }
  return -1;
};

// Print a node
void BTree::print_node(int page, const BNode& node) const {
  if (node.type() == NodeType::INTERNAL) {
    auto internal = static_cast<const BInternalNode&>(node);
    std::cout << "Internal node (ID: " << page << ", N: " << node.n_keys() << ", SIZE: " << internal.data_size()
              << ")\n\tPointers: ";
    for (size_t i = 0; i < internal.n_keys() + 1; ++i) {
      std::cout << internal.get_pointer(i) << " ";
    }
    std::cout << "\n\tOffsets: ";
    for (size_t i = 0; i < internal.n_keys() + 1; ++i) {
      std::cout << internal.get_offset(i) << " ";
    }
    std::cout << "\n\tKeys:\n\t\t";
    for (size_t i = 0; i < internal.n_keys(); ++i) {
      std::cout << internal.get_key(i).c_str() << "\n\t\t";
    }
    std::cout << std::endl;
    if (internal.n_keys() > 0) {
      for (size_t i = 0; i < internal.n_keys() + 1; ++i) {
        auto ptr = internal.get_pointer(i);
        auto child = get_node(store_driver->get(ptr));
        print_node(ptr, *child);
      }
    }
  } else if (node.type() == NodeType::LEAF) {
    auto leaf = static_cast<const BLeafNode&>(node);
    std::cout << "Leaf node (ID:" << page << ", N: " << node.n_keys() << ", SIZE: " << leaf.data_size()
              << ")\n\tOffsets: ";
    for (size_t i = 0; i < leaf.n_keys() + 1; ++i) {
      std::cout << leaf.get_offset(i) << " ";
    }
    std::cout << "\n\tKeys:\n\t\t";
    for (size_t i = 0; i < leaf.n_keys(); ++i) {
      std::cout << leaf.get_key(i).c_str() << ": " << leaf.get_value(i).c_str() << "\n\t\t";
    }
    std::cout << std::endl;
  } else {
    std::terminate();
  }
}

// Print full tree
void BTree::print() const {
  std::cout << "\n=====TREE=====" << std::endl;
  auto arr = store_driver->get(root);
  auto root_page = get_node(arr);
  print_node(root, *root_page);
}

}  // namespace cpp_database
