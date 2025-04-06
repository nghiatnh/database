#ifndef BYTE_ARRAY_H
#define BYTE_ARRAY_H

#include <bitset>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <vector>

namespace cpp_database {

class ByteArray {
 public:
  explicit ByteArray() : n{1} { data = new std::byte[n]; }
  explicit ByteArray(const std::string& s) : n{s.length()} {
    data = new std::byte[n];
    std::memcpy(data, s.data(), n);
  }
  explicit ByteArray(std::size_t _n) : n{_n} { data = new std::byte[n]; }
  explicit ByteArray(std::vector<std::byte>&& v) : n{v.size()} {
    data = new std::byte[n];
    std::memcpy(data, v.data(), n);
  }
  explicit ByteArray(const std::vector<std::byte>& v) : n{v.size()} {
    data = new std::byte[n];
    std::memcpy(data, v.data(), n);
  }
  ~ByteArray() { delete[] data; }
  explicit ByteArray(const ByteArray& v) : n{v.size()} {
    data = new std::byte[n];
    std::memcpy(data, v.data, n);
  }
  explicit ByteArray(ByteArray&& v) : n{v.size()} {
    data = new std::byte[n];
    std::memcpy(data, v.data, n);
  }
  ByteArray& operator=(ByteArray&&) = delete;

  inline std::string c_str() const { return std::string{cast_data<char>(), n}; }
  inline int c_int() const { return get<int32_t>(0); }
  inline int c_int64() const { return get<int64_t>(0); }
  inline int c_uint() const { return get<uint32_t>(0); }
  inline int c_uint64() const { return get<uint64_t>(0); }
  inline int c_double() const { return get<double>(0); }

  template <typename T>
  inline void set_value(size_t index, T value) {
    assert(index < n);
    cast_data<T>(index)[0] = value;
  }

  inline void set_value(size_t start, const ByteArray& other) {
    assert(start < n && start + other.n < n);
    std::memcpy(data + start, other.data, other.n);
  }

  template <typename T>
  inline void fill(T value) {
    std::memset(cast_data<T>(), value, cast_size<T>());
  }
  inline void reset_bytes() { fill(0); }
  inline size_t size() const { return n; }

  template <typename T>
  inline T get(size_t index) const {
    assert(index < n);
    return cast_data<T>(index)[0];
  }
  inline ByteArray slice(size_t start, size_t end) const {
    assert(start < end && end < n);
    ByteArray arr{end - start};
    std::memcpy(arr.data, data + start, end - start);
    return ByteArray{arr};
  }
  std::byte operator[](size_t index) const { return data[index]; }
  int operator>=(const ByteArray& other) const { return (c_str() >= other.c_str()); }
  int operator<=(const ByteArray& other) const { return (c_str() <= other.c_str()); }
  int operator<(const ByteArray& other) const { return (c_str() < other.c_str()); }
  int operator>(const ByteArray& other) const { return (c_str() > other.c_str()); }
  int operator==(const ByteArray& other) const { return (c_str() == other.c_str()); }
  int operator!=(const ByteArray& other) const { return (c_str() != other.c_str()); }

 private:
  size_t n;
  bool shallow;
  std::byte* data;

  template <typename T>
  inline T* cast_data() const {
    return reinterpret_cast<T*>(data);
  }

  template <typename T>
  inline T* cast_data(int start) const {
    return reinterpret_cast<T*>(data + start);
  }

  template <typename T>
  inline size_t cast_size() const {
    return n / sizeof(T);
  }
};

}  // namespace cpp_database

#endif  // !BYTE_ARRAY_H