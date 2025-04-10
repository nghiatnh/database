#include "stack.h"

namespace cpp_database {

size_t Stack::pop() {
  if (head == 0) {
    return 0;
  }
  auto top_page = StackNode(store_driver->get(head));
  if (offset < top_page.total_length()) {
    auto page_index = head;
    auto off = offset;
    while (off >= StackNode(store_driver->get(page_index)).n_pointers()) {
      off -= StackNode(store_driver->get(page_index)).n_pointers();
      page_index = StackNode(store_driver->get(page_index)).next_pointer();
    }
    auto node = StackNode(store_driver->get(page_index));
    auto ptr = node.get_pointer(node.n_pointers() - off - 1);
    ++offset;
    return ptr;
  }
  return 0;
}

// Reuse freed pages using the free pages of stack itself
void Stack::update(std::vector<size_t>&& freed) {
  // If do not pop and do not push anything => nothing to do
  if (offset == 0 && freed.size() == 0) {
    return;
  }
  auto total = total_length();
  auto off = offset;
  std::vector<size_t> reuse = {};
  while (head != 0 && reuse.size() * STACK_NODE_CAP < freed.size()) {
    auto node = StackNode(store_driver->get(head));
    freed.push_back(head);
    if (off >= node.n_pointers()) {
      // phase 1: remove all used (pop) nodes
      off -= node.n_pointers();
    } else {
      // phase 2: reuse pointers from stack itself
      auto remain = node.n_pointers() - off;
      off = 0;
      auto added_sz = freed.size() + remain;
      // How many pages need to save added_sz pointers?
      while (remain > 0 && reuse.size() * STACK_NODE_CAP < added_sz) {
        remain--;
        reuse.push_back(node.get_pointer(remain));
        added_sz = freed.size() + remain;
      }

      for (size_t i = 0; i < remain; ++i) {
        freed.push_back(node.get_pointer(i));
      }
    }
    total -= node.n_pointers();
    head = node.next_pointer();
  }
  _push(freed, reuse);
  auto top_page = StackNode(store_driver->get(head));
  top_page.set_total_length(total + freed.size());
  store_driver->use_page(head, top_page.data_arr());
  offset = 0;
}

void Stack::print() const {
  if (head == 0) {
    std::cout << "Empty Stack!" << std::endl;
    return;
  }
  size_t start = 0;
  auto total = total_length();
  auto page_index = head;
  StackNode page{store_driver->get(page_index)};
  std::cout << "Stack: ([" << head << "]";
  while (total > 0 && page_index != 0) {
    if (page.n_pointers() > 0) {
      std::cout << " " << page.get_pointer(page.n_pointers() - start - 1);
      ++start;
    }
    if (start == page.n_pointers()) {
      total -= start;
      start = 0;
      page_index = page.next_pointer();
      std::cout << ") -> ([" << page_index << "]";
      page.data_arr().set_value(0, store_driver->get(page_index));
    }
  }
  std::cout << ")" << std::endl;
}

inline void Stack::_push(const std::vector<size_t>& freed, const std::vector<size_t> reuse) {
  size_t start = 0;
  auto end = reuse.size();
  while (freed.size() > start) {
    auto new_node = StackNode(ByteArray{PAGE_SIZE});
    new_node.set_type();
    auto size = std::min(freed.size() - start, size_t(STACK_NODE_CAP));
    new_node.set_n_pointers(size);
    new_node.set_next_pointer(head);
    for (size_t i = 0; i < size; ++i) {
      new_node.set_pointer(i, freed[start + i]);
    }
    start += size;
    if (end > 0) {
      head = reuse[end - 1];
      store_driver->use_page(head, new_node.data_arr());
      --end;
    } else {
      head = store_driver->new_page(new_node.data_arr());
    }
  }
  // Handle case: reuse size: n, free_size: (n - 1) * STACK_NODE_CAP
  if (end > 0) {
    auto new_node = StackNode(ByteArray{PAGE_SIZE});
    new_node.set_type();
    new_node.set_n_pointers(0);
    new_node.set_next_pointer(head);
    head = reuse[end - 1];
    store_driver->use_page(head, new_node.data_arr());
  }
}

}  // namespace cpp_database
