#ifndef DRIVER_DRIVER_H
#define DRIVER_DRIVER_H

#include "byte_array.h"

namespace cpp_database::driver {

class IDriver {
 public:
  virtual bool has_page(int64_t page) const = 0;
  virtual ByteArray get(int64_t page) const = 0;
  virtual void delete_page(int64_t page) = 0;
  virtual int64_t new_page(const ByteArray&) = 0;

  virtual ~IDriver() = default;  // Always add virtual destructor for interfaces
};

}  // namespace cpp_database::driver

#endif  // !DRIVER_DRIVER_H