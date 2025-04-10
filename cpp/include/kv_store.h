#ifndef CPP_DATABASE_KV_STORE_H
#define CPP_DATABASE_KV_STORE_H

#include <map>

#include "b_tree.h"
#include "byte_array.h"
#include "driver/driver.h"
#include "master_page.h"
#include "stack.h"

namespace cpp_database {

class BTreeDriver;
class StackDriver;

class KVStore {
 public:
  KVStore(driver::IIODriver *_driver)
      : io_driver{_driver}, tree{nullptr}, stack{nullptr}, master_page{}, freed{}, updates{}, n_added{0} {
    auto tree_driver = std::make_unique<BTreeDriver>(this);
    auto stack_driver = std::make_unique<StackDriver>(this);
    tree = std::make_unique<BTree>(tree_driver.release());
    stack = std::make_unique<Stack>(stack_driver.release());
  }
  ~KVStore() {}

  inline void master_load() {
    if (io_driver->size() < PAGE_SIZE) {
      master_page = MasterPage{};
    } else {
      master_page = MasterPage{io_driver->read(0, PAGE_SIZE)};
    }
    tree->set_root(master_page.root);
    stack->set_head(master_page.head);
  }

  inline void master_save() {
    if (io_driver->size() < PAGE_SIZE) {
      io_driver->extend(PAGE_SIZE);
      master_page.n_flushed = 1;
    }
    io_driver->write(0, master_page.serialize());
  }

  inline void insert(const std::string &key, const std::string &value) { insert(ByteArray{key}, ByteArray{value}); }
  inline void remove(const std::string &key) { remove(ByteArray{key}); }

  inline const BTree *get_tree() { return tree.get(); }
  inline const Stack *get_stack() { return stack.get(); }

  void insert(const ByteArray &key, const ByteArray &value);
  void remove(const ByteArray &key);
  void flush();

 private:
  driver::IIODriver *io_driver;
  std::unique_ptr<BTree> tree;
  std::unique_ptr<Stack> stack;
  MasterPage master_page;
  std::vector<size_t> freed;
  std::map<size_t, ByteArray> updates;
  size_t n_added;

  ByteArray get_page(size_t page) const {
    if (updates.contains(page)) {
      return ByteArray{updates.at(page)};
    }
    return io_driver->read(page * PAGE_SIZE, PAGE_SIZE);
  }

  friend class BTreeDriver;
  friend class StackDriver;
};

class BTreeDriver : public driver::IBTreeDriver {
 public:
  BTreeDriver(KVStore *ptr) : store_ptr{ptr} {}

  ByteArray get(size_t page) const override { return store_ptr->get_page(page); }
  void delete_page(size_t page) override { store_ptr->freed.push_back(page); }
  size_t new_page(const ByteArray &arr) override {
    auto page = store_ptr->stack->pop();
    if (page != 0) {
      if (store_ptr->updates.contains(page)) {
        store_ptr->updates[page] = arr;
      } else {
        store_ptr->updates.insert(std::pair{page, ByteArray{arr}});
      }
      return page;
    }
    page = store_ptr->master_page.n_flushed + store_ptr->n_added;
    ++store_ptr->n_added;
    store_ptr->updates.insert(std::pair{page, ByteArray{arr}});
    return page;
  }

 private:
  KVStore *store_ptr;
};

class StackDriver : public driver::IStackDriver {
 public:
  StackDriver(KVStore *ptr) : store_ptr{ptr} {}
  ByteArray get(size_t page) const { return store_ptr->get_page(page); }
  void use_page(size_t page, const ByteArray &arr) {
    if (store_ptr->updates.contains(page)) {
      store_ptr->updates[page] = arr;
    } else {
      store_ptr->updates.insert(std::pair{page, ByteArray{arr}});
    }
  }
  size_t new_page(const ByteArray &arr) {
    size_t page = store_ptr->master_page.n_flushed + store_ptr->n_added;
    ++store_ptr->n_added;
    store_ptr->updates.insert(std::pair{page, ByteArray{arr}});
    return page;
  }

 private:
  KVStore *store_ptr;
};

}  // namespace cpp_database

#endif  // !CPP_DATABASE_KV_STORE_H