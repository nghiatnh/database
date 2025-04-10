#ifndef CPP_DATABASE_DRIVER_MEMORY_H
#define CPP_DATABASE_DRIVER_MEMORY_H

#include <iostream>
#include <map>

#include "driver/driver.h"

namespace cpp_database::driver {

// For dev/test only
class MemoryDriver : public IBTreeDriver, public IStackDriver {
 public:
  explicit MemoryDriver() { data = {}; }

  ByteArray get(size_t page) const override { return ByteArray{data.at(page)}; };
  void delete_page(size_t page) override { data.erase(page); };
  size_t new_page(const ByteArray &arr) override {
    data.insert(std::pair{n_page, ByteArray{arr}});
    ++n_page;
    return n_page - 1;
  };
  void use_page(size_t page, const ByteArray &arr) override {
    data[page].set_value(0, arr.slice(0, data[page].size()));
  };

 private:
  int n_page;
  std::map<size_t, ByteArray> data;
};

class MemoryIO : public IIODriver {
  MemoryIO() { data = ByteArray{0}; }
  bool open() { return true; }
  bool close() { return true; }
  size_t size() { return data.size(); }
  ByteArray read(size_t offset, size_t size) { return data.slice(offset, offset + size); }
  void write(size_t offset, const ByteArray &_data) { data.set_value(offset, _data); }
  void flush() {}
  void extend(size_t size) {
    ByteArray old_data = ByteArray{data};
    data = ByteArray{size};
    data.set_value(0, old_data);
  }

 private:
  ByteArray data;
};

}  // namespace cpp_database::driver

#endif  // !CPP_DATABASE_DRIVER_MEMORY_H