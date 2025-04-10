#ifndef CPP_DATABASE_STACK_H
#define CPP_DATABASE_STACK_H

#include <cstddef>
#include <iostream>

#include "debug.h"
#include "driver/driver.h"
#include "stack_node.h"

namespace cpp_database {

const static int STACK_NODE_CAP = (PAGE_SIZE - (NODE_TYPE_SZ + 2 * N_KEY_SZ)) / POINTER_SZ;

struct Stack {
 public:
  Stack(driver::IStackDriver* _driver) : head{0}, offset{0}, store_driver{_driver} {}
  Stack(driver::IStackDriver* _driver, size_t _head) : head{_head}, offset{0}, store_driver{_driver} {}
  ~Stack() {}

  inline size_t total_length() const {
    if (head == 0) {
      return 0;
    }
    return StackNode(store_driver->get(head)).total_length();
  }

  size_t pop();
  // Reuse freed pages using the free pages of stack itself
  void update(std::vector<size_t>&& freed);
  void print() const;

  inline size_t get_head() const { return head; }
  inline void set_head(size_t _head) { head = _head; }
  inline size_t get_offset() const { return offset; }

 private:
  size_t head;
  size_t offset;
  driver::IStackDriver* store_driver;

  inline void _push(const std::vector<size_t>& freed, const std::vector<size_t> reuse);
};

}  // namespace cpp_database

#endif  // !CPP_DATABASE_STACK_H