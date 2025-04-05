#ifndef B_TREE_H
#define B_TREE_H

#include <cstdint>
#include <vector>

#include "b_node.h"
#include "driver/driver.h"

namespace cpp_database {

class BTree {
 public:
  BTree(std::unique_ptr<driver::IDriver> sd) : root{0} { store_driver = std::move(sd); }

  void insert(const std::vector<std::byte> &key, const std::vector<std::byte> &value) {
    insert(ByteArray{key}, ByteArray{value});
  }
  void insert(const ByteArray &key, const ByteArray &value);
  void remove(const std::vector<std::byte> &key) { remove(ByteArray{key}); }
  void remove(const ByteArray &key);
  inline size_t get_root() const { return root; }

  inline const driver::IDriver *get_driver() const { return store_driver.get(); }

  void print();

 private:
  size_t root;
  std::unique_ptr<driver::IDriver> store_driver;

  BInternalNode insert_node(BInternalNode &&node, const ByteArray &key, const ByteArray &value);

  BLeafNode insert_node(BLeafNode &&node, const ByteArray &key, const ByteArray &value);

  size_t search_key(const BNode *node, const ByteArray &key) const;

  BInternalNode split_node(BInternalNode &&parent, size_t index, BLeafNode &&node);
  BInternalNode split_node(BInternalNode &&parent, size_t index, BInternalNode &&node);

  BInternalNode remove_node(BInternalNode &&node, const ByteArray &key);

  BLeafNode remove_node(BLeafNode &&node, const ByteArray &key);

  BInternalNode merge_node(BInternalNode &&parent, size_t index, BLeafNode &&node);
  BInternalNode merge_node(BInternalNode &&parent, size_t index, BInternalNode &&node);

  void print_node(int page, const BNode *node);
};

}  // namespace cpp_database

#endif  // !B_TREE_H