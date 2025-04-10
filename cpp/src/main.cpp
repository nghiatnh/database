#include <bitset>
#include <string>

#include "b_tree.h"
#include "debug.h"
#include "driver/memory.h"
#include "stack.h"

using namespace cpp_database;

int main() {
  {
    auto t = debug::TimeWatcher();
    auto sd = std::make_unique<driver::MemoryDriver>();
    for (size_t i = 0; i < 100; ++i) {
      sd->new_page(ByteArray{PAGE_SIZE});
    }
    Stack stk{sd.get(), 0};
    stk.update(std::vector<size_t>{1, 2, 3, 4, 5, 6, 7, 8, 9});
    stk.print();
    std::cout << "--pop " << stk.pop() << std::endl;
    stk.update(std::vector<size_t>{10});
    stk.print();
    std::cout << "--pop " << stk.pop() << std::endl;
    std::cout << "--pop " << stk.pop() << std::endl;
    std::cout << "--pop " << stk.pop() << std::endl;
    stk.update(std::vector<size_t>{9});
    stk.print();
    stk.update(std::vector<size_t>{10});
    stk.print();
    std::cout << "--pop " << stk.pop() << std::endl;
    std::cout << "--pop " << stk.pop() << std::endl;
    std::cout << "--pop " << stk.pop() << std::endl;
    std::cout << "--pop " << stk.pop() << std::endl;
    stk.update(std::vector<size_t>{});
    stk.print();
  }
  return 0;
}