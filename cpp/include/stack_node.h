#ifndef CPP_DATABASE_STACK_NODE_H
#define CPP_DATABASE_STACK_NODE_H

#include "byte_array.h"
#include "constants.h"

namespace cpp_database {

// StackNode Structure:
// | Node_Type | Total | N_Pointers | Next_Pointer | Pointers... |
// |-----------|-------|------------|--------------|-------------|
// | 1B        | 8B    | 8B         | 8B           | 8B * N      |
struct StackNode {
 public:
  StackNode(ByteArray _data) : data{_data} {}
  ~StackNode() {}

  inline NodeType type() const { return NodeType(data.get<uint8_t>(0)); }
  inline void set_type() { data.set_value<uint8_t>(0, uint8_t(NodeType::STACK)); }
  inline size_t total_length() const { return data.get<size_t>(NODE_TYPE_SZ); }
  inline void set_total_length(size_t total) { data.set_value(NODE_TYPE_SZ, total); }
  inline size_t n_pointers() const { return data.get<size_t>(NODE_TYPE_SZ + N_KEY_SZ); }
  inline void set_n_pointers(size_t n) { data.set_value(NODE_TYPE_SZ + N_KEY_SZ, n); }
  inline size_t next_pointer() const { return data.get<size_t>(NODE_TYPE_SZ + 2 * N_KEY_SZ); }
  inline void set_next_pointer(size_t next) { data.set_value(NODE_TYPE_SZ + 2 * N_KEY_SZ, next); }
  inline size_t get_pointer(size_t index) const {
    return data.get<size_t>(NODE_TYPE_SZ + 2 * N_KEY_SZ + (index + 1) * POINTER_SZ);
  }
  inline void set_pointer(size_t index, size_t ptr) {
    data.set_value(NODE_TYPE_SZ + 2 * N_KEY_SZ + (index + 1) * POINTER_SZ, ptr);
  }
  inline ByteArray& data_arr() { return data; }

 private:
  ByteArray data;
};

}  // namespace cpp_database

#endif  // !CPP_DATABASE_STACK_NODE_H