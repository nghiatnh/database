#include "kv_store.h"

#include <iostream>

#include "debug.h"

namespace cpp_database {

void KVStore::insert(const ByteArray &key, const ByteArray &value) {
  tree->insert(key, value);
  flush();
}

void KVStore::update(const ByteArray &key, const ByteArray &value) {
  tree->update(key, value);
  flush();
}

void KVStore::remove(const ByteArray &key) {
  tree->remove(key);
  flush();
}

void KVStore::flush() {
  stack->update(std::move(freed));
  auto n_flushed = master_page.n_flushed + n_added;
  io_driver->extend(n_flushed * PAGE_SIZE);
  for (auto [page, arr] : updates) {
    io_driver->write(page * PAGE_SIZE, arr);
  }
  freed = {};
  n_added = 0;
  updates.clear();
  master_page.n_flushed = n_flushed;
  master_page.root = tree->get_root();
  master_page.head = stack->get_head();
  master_save();
}

}  // namespace cpp_database
