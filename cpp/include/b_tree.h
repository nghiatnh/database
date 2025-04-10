#ifndef CPP_DATABASE_B_TREE_H
#define CPP_DATABASE_B_TREE_H

#include <cstdint>
#include <vector>

#include "b_node.h"
#include "driver/driver.h"

namespace cpp_database {

class BTree {
 public:
  BTree(driver::IBTreeDriver *sd) : root{0} { store_driver = sd; }

  inline void insert(const std::vector<std::byte> &key, const std::vector<std::byte> &value) {
    insert(ByteArray{key}, ByteArray{value});
  }
  inline void insert(const std::string &key, const std::string &value) { insert(ByteArray{key}, ByteArray{value}); }
  void insert(const ByteArray &key, const ByteArray &value);

  inline void remove(const std::vector<std::byte> &key) { remove(ByteArray{key}); }
  inline void remove(const std::string &key) { remove(ByteArray{key}); }
  void remove(const ByteArray &key);

  inline size_t get_root() const { return root; }
  inline bool is_empty() const { return root == 0; }
  inline const driver::IBTreeDriver *get_driver() const { return store_driver; }

  void print() const;

 private:
  size_t root;
  driver::IBTreeDriver *store_driver;

  std::unique_ptr<BNode> insert_node(const BNode &node, const ByteArray &key, const ByteArray &value) const;

  std::unique_ptr<BNode> remove_node(const BNode &node, const ByteArray &key) const;

  size_t search_key(const BNode &node, const ByteArray &key) const;
  int search_exact_key(const BLeafNode &node, const ByteArray &key) const;

  inline std::unique_ptr<BInternalNode> split_node(const BInternalNode &parent, size_t index, const BNode &node) const {
    if (node.type() == NodeType::LEAF) {
      return split_node(parent, index, static_cast<const BLeafNode &>(node));
    } else {
      return split_node(parent, index, static_cast<const BInternalNode &>(node));
    }
  }
  std::unique_ptr<BInternalNode> split_node(const BInternalNode &parent, size_t index, const BLeafNode &node) const;
  std::unique_ptr<BInternalNode> split_node(const BInternalNode &parent, size_t index, const BInternalNode &node) const;

  inline std::unique_ptr<BNode> merge_node(const BInternalNode &parent, size_t index, const BNode &left,
                                           const BNode &right) const {
    if (left.type() == NodeType::LEAF) {
      return merge_node(parent, index, static_cast<const BLeafNode &>(left), static_cast<const BLeafNode &>(right));
    } else {
      return merge_node(parent, index, static_cast<const BInternalNode &>(left),
                        static_cast<const BInternalNode &>(right));
    }
  }
  std::unique_ptr<BNode> merge_node(const BInternalNode &parent, size_t index, const BLeafNode &left,
                                    const BLeafNode &right) const;
  std::unique_ptr<BNode> merge_node(const BInternalNode &parent, size_t index, const BInternalNode &left,
                                    const BInternalNode &right) const;

  void print_node(int page, const BNode &node) const;
};

}  // namespace cpp_database

#endif  // !CPP_DATABASE_B_TREE_H