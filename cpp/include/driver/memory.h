#ifndef DRIVER_MEMORY_H
#define DRIVER_MEMORY_H

#include <iostream>
#include <map>

#include "driver/driver.h"

namespace cpp_database::driver {
class MemoryDriver : public IDriver {
 public:
  explicit MemoryDriver() { data = {}; }

  bool has_page(int64_t page) const override { return data.contains(page); };
  ByteArray get(int64_t page) const override { return ByteArray{data.at(page)}; };
  void delete_page(int64_t page) override {
    data.erase(page);
  };
  int64_t new_page(const ByteArray& arr) override {
    data.insert(std::pair{n_page, ByteArray{arr}});
    ++n_page;
    return n_page - 1;
  };

 private:
  int n_page;
  std::map<int64_t, ByteArray> data;
};
}  // namespace cpp_database::driver

#endif  // !DRIVER_MEMORY_H