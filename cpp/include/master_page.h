#ifndef CPP_DATABASE_MASTER_PAGE_H
#define CPP_DATABASE_MASTER_PAGE_H

#include <cstddef>

#include "byte_array.h"
#include "constants.h"

namespace cpp_database {

// | DB_SIGNATURE | root | head | n_flushed |
// |--------------|------|------|-----------|
// | 16B          | 8B   | 8B   | 8B        |
struct MasterPage {
  ByteArray signature = ByteArray{DB_SIGNATURE};
  size_t root = 0;
  size_t head = 0;
  size_t n_flushed = 0;

  MasterPage() = default;
  MasterPage(const ByteArray& arr) {
    signature = arr.slice(0, DB_SIGNATURE_SZ);
    root = arr.get<size_t>(DB_SIGNATURE_SZ);
    head = arr.get<size_t>(DB_SIGNATURE_SZ + POINTER_SZ);
    n_flushed = arr.get<size_t>(DB_SIGNATURE_SZ + POINTER_SZ + POINTER_SZ);
  }

  ByteArray serialize() {
    ByteArray arr{PAGE_SIZE};
    arr.set_value(0, signature);
    arr.set_value(DB_SIGNATURE_SZ, root);
    arr.set_value(DB_SIGNATURE_SZ + POINTER_SZ, head);
    arr.set_value(DB_SIGNATURE_SZ + POINTER_SZ + POINTER_SZ, n_flushed);
  }
};

}  // namespace cpp_database

#endif  // !CPP_DATABASE_MASTER_PAGE_H