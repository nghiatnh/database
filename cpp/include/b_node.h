#ifndef B_NODE_H
#define B_NODE_H

#include <byte_array.h>

#include <bitset>
#include <iostream>
#include <map>
#include <string>
#include <vector>

#include "constants.h"
#include "debug.h"

namespace cpp_database {

enum class NodeType : uint8_t {
  EMPTY,
  LEAF,
  INTERNAL,
};

struct BNode {
 public:
  BNode(const ByteArray& _data) : data{_data} {}
  virtual ~BNode() {}

  inline NodeType type() const { return NodeType{data.get<uint8_t>(0)}; }
  inline void set_type(NodeType node_type) { data.set_value(0, std::byte(node_type)); }

  inline size_t n_keys() const { return data.get<size_t>(NODE_TYPE_SZ); }
  inline void set_n_keys(size_t sz) { data.set_value(NODE_TYPE_SZ, sz); }

  inline size_t data_size() const { return key_start() + get_offset(n_keys()); }

  virtual size_t key_start() const = 0;

  virtual ByteArray get_key(size_t index) const = 0;

  virtual size_t get_offset(size_t index) const = 0;
  virtual void set_offset(size_t index, size_t offset) = 0;

  inline const ByteArray& data_arr() const { return data; }

 protected:
  ByteArray data;
};

// Node type | N Keys | Offsets | Key-Value
// 1B        | 8B     | N * 8B  | ...
// Key Size | Value Size | Key           | Value
// 8B       | 8B         | Key Size * 1B | Value Size * 1B
struct BLeafNode : public BNode {
 public:
  BLeafNode(const ByteArray& _data) : BNode(_data) {}
  ~BLeafNode() override {}

  size_t key_start() const override { return NODE_TYPE_SZ + N_KEY_SZ + n_keys() * OFFSET_SZ; }

  size_t get_offset(size_t index) const override {
    if (index == 0) return 0;
    return data.get<size_t>(NODE_TYPE_SZ + N_KEY_SZ + (index - 1) * OFFSET_SZ);
  }
  void set_offset(size_t index, size_t offset) override {
    if (index == 0) return;
    return data.set_value(NODE_TYPE_SZ + N_KEY_SZ + (index - 1) * OFFSET_SZ, offset);
  }

  ByteArray get_key(size_t index) const override {
    auto offset = key_start() + get_offset(index);
    auto key_sz = data.get<size_t>(offset);
    auto start = offset + 2 * KV_SIZE_SZ;
    return data.slice(start, start + key_sz);
  }
  inline ByteArray get_value(int index) const {
    auto offset = key_start() + get_offset(index);
    auto key_sz = data.get<size_t>(offset);
    auto value_sz = data.get<size_t>(offset + KV_SIZE_SZ);
    auto start = offset + 2 * KV_SIZE_SZ + key_sz;
    return data.slice(start, start + value_sz);
  }
  inline void set_key_value(int index, const ByteArray& key, const ByteArray& value) {
    auto kv_pos = key_start() + get_offset(index);
    data.set_value(kv_pos, key.size());
    data.set_value(kv_pos + KV_SIZE_SZ, value.size());
    data.set_value(kv_pos + 2 * KV_SIZE_SZ, key);
    data.set_value(kv_pos + 2 * KV_SIZE_SZ + key.size(), value);
  }

  BLeafNode insert_key(size_t index, const ByteArray& key, const ByteArray& value) const {
    BLeafNode node{ByteArray{data.size()}};
    node.set_type(type());
    node.set_n_keys(n_keys() + 1);
    for (size_t i = 0; i <= index; ++i) {
      node.set_offset(i, get_offset(i));
    }
    auto add_sz = 2 * KV_SIZE_SZ + key.size() + value.size();
    for (size_t i = index + 1; i < node.n_keys() + 1; ++i) {
      node.set_offset(i, get_offset(i - 1) + add_sz);
    }
    for (size_t i = 0; i < index; ++i) {
      node.set_key_value(i, get_key(i), get_value(i));
    }
    node.set_key_value(index, key, value);
    for (size_t i = index + 1; i < node.n_keys(); ++i) {
      node.set_key_value(i, get_key(i - 1), get_value(i - 1));
    }
    return node;
  }

  BLeafNode remove_key(size_t index) const {
    BLeafNode node{ByteArray{data.size()}};
    node.set_type(type());
    node.set_n_keys(n_keys() - 1);
    for (size_t i = 0; i < index; ++i) {
      node.set_offset(i, get_offset(i));
    }
    auto remove_sz = get_offset(index + 1) - get_offset(index);
    for (size_t i = index; i < node.n_keys() + 1; ++i) {
      node.set_offset(i, get_offset(i + 1) - remove_sz);
    }
    for (size_t i = 0; i < index; ++i) {
      node.set_key_value(i, get_key(i), get_value(i));
    }
    for (size_t i = index; i < node.n_keys(); ++i) {
      node.set_key_value(i, get_key(i + 1), get_value(i + 1));
    }
    return node;
  }
};

// Node type | N Keys | Pointers          | Key Offsets | Keys
// 1B        | 8B     | (N Keys + 1) * 8B | N Keys * 8B | ...
struct BInternalNode : public BNode {
 public:
  BInternalNode(const ByteArray& _data) : BNode(_data) {}
  ~BInternalNode() override {}

  size_t key_start() const override {
    return NODE_TYPE_SZ + N_KEY_SZ + (n_keys() + 1) * POINTER_SZ + n_keys() * OFFSET_SZ;
  }

  ByteArray get_key(size_t index) const override {
    auto start = key_start() + get_offset(index);
    auto end = key_start() + get_offset(index + 1);
    return data.slice(start, end);
  }
  inline void set_key(size_t index, const ByteArray& key) {
    data.set_value(key_start() + get_offset(index), key);
  }

  size_t get_offset(size_t index) const override {
    if (index == 0) return 0;
    return data.get<size_t>(NODE_TYPE_SZ + N_KEY_SZ + (n_keys() + 1) * POINTER_SZ +
                            (index - 1) * OFFSET_SZ);
  }
  inline void set_offset(size_t index, size_t offset) {
    if (index == 0) return;
    data.set_value(NODE_TYPE_SZ + N_KEY_SZ + (n_keys() + 1) * POINTER_SZ + (index - 1) * OFFSET_SZ,
                   offset);
  }

  inline size_t get_pointer(size_t index) const {
    return data.get<size_t>(NODE_TYPE_SZ + N_KEY_SZ + index * POINTER_SZ);
  }
  inline void set_pointer(size_t index, size_t ptr) {
    data.set_value(NODE_TYPE_SZ + N_KEY_SZ + index * POINTER_SZ, ptr);
  }
};

inline std::unique_ptr<BNode> get_node(const ByteArray& arr) {
  assert(NodeType(arr.get<std::byte>(0)) != NodeType::EMPTY);
  if (NodeType(arr.get<std::byte>(0)) == NodeType::INTERNAL) {
    return std::make_unique<BInternalNode>(arr);
  } else {
    return std::make_unique<BLeafNode>(arr);
  }
}

}  // namespace cpp_database

#endif  // !B_NODE_H