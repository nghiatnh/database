#include "b_tree.h"

#include <iostream>

#include "b_node.h"
#include "constants.h"
#include "debug.h"

using namespace std;

namespace cpp_database {

// Insert a key-value pair
void BTree::insert(const ByteArray& key, const ByteArray& value) {
  if (!store_driver->has_page(root)) {
    ByteArray arr{2 * PAGE_SIZE};
    arr.set_value<byte>(0, static_cast<byte>(NodeType::LEAF));
    arr.set_value<size_t>(1, 0);
    root = store_driver->new_page(arr);
  }
  auto root_page = make_unique<BNode>(store_driver->get(root));
  auto old_root = root;
  if (root_page->type() == NodeType::INTERNAL) {
    auto internal = static_cast<BInternalNode*>(root_page.release());
    auto result = insert_node(move(*internal), key, value);
    if (result.data_size() > PAGE_SIZE) {
      BInternalNode parent{ByteArray{2 * PAGE_SIZE}};
      parent.set_type(NodeType::INTERNAL);
      parent.set_n_keys(0);
      auto new_node = split_node(move(parent), 0, move(result));
      root = store_driver->new_page(new_node.data_arr());
    } else {
      root = store_driver->new_page(result.data_arr());
    }
  } else if (root_page->type() == NodeType::LEAF) {
    auto leaf = static_cast<BLeafNode*>(root_page.release());
    auto result = insert_node(move(*leaf), key, value);
    if (result.data_size() > PAGE_SIZE) {
      BInternalNode parent{ByteArray{2 * PAGE_SIZE}};
      parent.set_type(NodeType::INTERNAL);
      parent.set_n_keys(0);
      auto new_node = split_node(move(parent), 0, move(result));
      root = store_driver->new_page(new_node.data_arr());
    } else {
      root = store_driver->new_page(result.data_arr());
    }
  }
  store_driver->delete_page(old_root);
}

// Insert Internal
BInternalNode BTree::insert_node(BInternalNode&& node, const ByteArray& key,
                                 const ByteArray& value) {
  auto offset = search_key(static_cast<const BNode*>(&node), key);
  auto page = node.get_pointer(offset);
  auto page_node = make_unique<BNode>(store_driver->get(page));
  if (page_node->type() == NodeType::INTERNAL) {
    auto internal = static_cast<BInternalNode*>(page_node.release());
    auto result = insert_node(move(*internal), key, value);
    if (result.data_size() > PAGE_SIZE) {
      auto new_node = split_node(move(node), offset, move(result));
      store_driver->delete_page(page);
      return new_node;
    }
    auto result_page = store_driver->new_page(result.data_arr());
    node.set_pointer(offset, result_page);
    store_driver->delete_page(page);
    return node;
  } else {
    auto leaf = static_cast<BLeafNode*>(page_node.release());
    auto result = insert_node(move(*leaf), key, value);
    if (result.data_size() > PAGE_SIZE) {
      auto new_node = split_node(move(node), offset, move(result));
      store_driver->delete_page(page);
      return new_node;
    }
    auto result_page = store_driver->new_page(result.data_arr());
    node.set_pointer(offset, result_page);
    store_driver->delete_page(page);
    return node;
  }
}

// Insert Leaf
BLeafNode BTree::insert_node(BLeafNode&& node, const ByteArray& key, const ByteArray& value) {
  auto index = search_key(static_cast<const BNode*>(&node), key);
  auto result = node.insert_key(index, key, value);
  return result;
}

// Split internal node
BInternalNode BTree::split_node(BInternalNode&& parent, size_t index, BLeafNode&& node) {
  size_t n_left = (node.n_keys() + 1) / 2;
  size_t n_right = node.n_keys() - n_left;

  BLeafNode left{ByteArray{2 * PAGE_SIZE}};
  BLeafNode right{ByteArray{2 * PAGE_SIZE}};
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
  return new_parent;
}

// Split leaf node
BInternalNode BTree::split_node(BInternalNode&& parent, size_t index, BInternalNode&& node) {
  size_t n_left = (node.n_keys() + 1) / 2;
  auto n_right = node.n_keys() - n_left;

  BInternalNode left{ByteArray{2 * PAGE_SIZE}};
  BInternalNode right{ByteArray{2 * PAGE_SIZE}};
  left.set_type(NodeType::INTERNAL);
  right.set_type(NodeType::INTERNAL);
  left.set_n_keys(n_left - 1);
  right.set_n_keys(n_right);
  for (size_t i = 0; i < n_left; ++i) {
    left.set_offset(i, node.get_offset(i));
  }
  for (size_t i = n_left; i < node.n_keys() + 1; ++i) {
    right.set_offset(i - n_left, node.get_offset(i) - node.get_offset(n_left));
  }
  for (size_t i = 0; i < n_left; ++i) {
    left.set_pointer(i, node.get_pointer(i));
  }
  for (size_t i = n_left; i < node.n_keys() + 1; ++i) {
    right.set_pointer(i - n_left, node.get_pointer(i));
  }
  for (size_t i = 0; i < n_left - 1; ++i) {
    left.set_key(i, node.get_key(i));
  }
  for (size_t i = n_left; i < node.n_keys(); ++i) {
    right.set_key(i - n_left, node.get_key(i));
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
  return new_parent;
}

// Search key
size_t BTree::search_key(const BNode* node, const ByteArray& key) const {
  if (node->n_keys() == 0) return 0;
  for (size_t i = 0; i < node->n_keys(); ++i) {
    if (node->type() == NodeType::INTERNAL) {
      auto internal = *static_cast<const BInternalNode*>(node);
      if (internal.get_key(i) >= key) {
        return i;
      }
    } else {
      auto leaf = *static_cast<const BLeafNode*>(node);
      if (leaf.get_key(i) >= key) {
        return i;
      }
    }
  }
  return node->n_keys();
};

// Print a node
void BTree::print_node(int page, const BNode* node) {
  if (node->type() == NodeType::INTERNAL) {
    auto internal = *static_cast<const BInternalNode*>(node);
    std::cout << "Internal node (ID: " << page << ", N: " << node->n_keys()
              << ", SIZE: " << internal.data_size() << ")\n\tPointers: ";
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
        auto n = BNode(store_driver->get(ptr));
        print_node(ptr, &n);
      }
    }
  } else if (node->type() == NodeType::LEAF) {
    auto leaf = *static_cast<const BLeafNode*>(node);
    std::cout << "Leaf node (ID:" << page << ", N: " << node->n_keys()
              << ", SIZE: " << leaf.data_size() << ")\n\tOffsets: ";
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
void BTree::print() {
  std::cout << "\n=====TREE=====" << std::endl;
  auto arr = store_driver->get(root);
  auto root_page = BNode(arr);
  print_node(root, &root_page);
}

}  // namespace cpp_database
