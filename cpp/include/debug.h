#ifndef CPP_DATABASE_DEBUG_H
#define CPP_DATABASE_DEBUG_H

#include <chrono>
#include <iostream>

#ifndef NDEBUG
#define __DEBUG__ (std::cout << __FILE__ << ":" << __LINE__ << std::endl);
#else
#define __DEBUG__
#endif

namespace cpp_database::debug {
class TimeWatcher {
#ifndef NDEBUG
 public:
  TimeWatcher() { start_time = std::chrono::high_resolution_clock::now(); }
  ~TimeWatcher() {
    auto end_time = std::chrono::high_resolution_clock::now();
    std::cout
        << "Total run time: "
        << std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time).count()
        << " micro seconds." << std::endl;
  }

 private:
  std::chrono::_V2::system_clock::time_point start_time;
#else
 public:
  TimeWatcher() {}
  ~TimeWatcher() {}
#endif
};
}  // namespace cpp_database::debug

#endif  // !CPP_DATABASE_DEBUG_H