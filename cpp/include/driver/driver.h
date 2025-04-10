#ifndef CPP_DATABASE_DRIVER_DRIVER_H
#define CPP_DATABASE_DRIVER_DRIVER_H

#include "byte_array.h"

namespace cpp_database::driver {

class IBTreeDriver {
 public:
  virtual ByteArray get(size_t page) const = 0;
  virtual void delete_page(size_t page) = 0;
  virtual size_t new_page(const ByteArray &arr) = 0;

  virtual ~IBTreeDriver() = default;  // Always add virtual destructor for interfaces
};

class IStackDriver {
 public:
  virtual ByteArray get(size_t page) const = 0;
  virtual void use_page(size_t page, const ByteArray &arr) = 0;
  virtual size_t new_page(const ByteArray &arr) = 0;

  virtual ~IStackDriver() = default;  // Always add virtual destructor for interfaces
};

class IIODriver {
 public:
  virtual bool open() = 0;
  virtual bool close() = 0;
  virtual size_t size() = 0;
  virtual ByteArray read(size_t offset, size_t size) = 0;
  virtual void write(size_t offset, const ByteArray &data) = 0;
  virtual void flush() = 0;
  virtual void extend(size_t size) = 0;

  virtual ~IIODriver() = default;  // Always add virtual destructor for interfaces
};

}  // namespace cpp_database::driver

#endif  // !CPP_DATABASE_DRIVER_DRIVER_H