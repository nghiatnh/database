#include <bitset>
#include <string>

#include "b_tree.h"
#include "debug.h"
#include "driver/memory.h"
#include "kv_store.h"
#include "stack.h"

using namespace cpp_database;

void test_stack() {
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
  stk.update(std::vector<size_t>{11});
  stk.print();
  std::cout << "--pop " << stk.pop() << std::endl;
  std::cout << "--pop " << stk.pop() << std::endl;
  std::cout << "--pop " << stk.pop() << std::endl;
  std::cout << "--pop " << stk.pop() << std::endl;
  stk.update(std::vector<size_t>{});
  stk.print();
}

void test_btree() {
  auto t = debug::TimeWatcher();
  auto sd = std::make_unique<driver::MemoryDriver>();
  BTree tree(sd.get());
  tree.insert(std::string{"hello"}, std::string{"world"});
  tree.insert(std::string{"i'm"}, std::string{"nghia"});
  tree.insert(std::string{"i'mm"}, std::string{"bioturi"});
  tree.insert(std::string{"nghia"}, std::string{"bioturi"});
  tree.insert(std::string{"mghia"}, std::string{"bioturi"});
  tree.insert(std::string{"hghia"}, std::string{"bioturi"});
  tree.insert(std::string{"nh"}, std::string{"bioturi"});
  tree.insert(std::string{"absldk"}, std::string{"bioturi"});
  tree.insert(std::string{"adb"}, std::string{"bioturi"});
  tree.insert(std::string{"cdb"}, std::string{"bioturi"});
  tree.insert(std::string{"ddb"}, std::string{"bioturi"});
  tree.insert(std::string{"fdb"}, std::string{"bioturi"});
  tree.insert(std::string{"ohhkhkk"}, std::string{"bioturi"});
  tree.insert(std::string{"ph"}, std::string{"bioturi"});
  tree.insert(std::string{"qhh"}, std::string{"bioturi"});
  tree.insert(std::string{"qhk"}, std::string{"bioturi"});
  tree.insert(std::string{"qhl"}, std::string{"bioturi"});
  tree.insert(std::string{"rh"}, std::string{"bioturi"});
  tree.insert(std::string{"yh"}, std::string{"bioturi"});
  tree.print();
  tree.remove(std::string{"i'm"});
  tree.remove(std::string{"hello"});
  tree.remove(std::string{"mghia"});
  tree.remove(std::string{"i'mm"});
  tree.remove(std::string{"nghia"});
  tree.remove(std::string{"nh"});
  tree.remove(std::string{"hghia"});
  tree.remove(std::string{"absldk"});
  tree.remove(std::string{"adb"});
  tree.remove(std::string{"cdb"});
  tree.remove(std::string{"ohhkhkk"});
  tree.remove(std::string{"ddb"});
  tree.remove(std::string{"fdb"});
  tree.remove(std::string{"qhl"});
  tree.remove(std::string{"yh"});
  tree.remove(std::string{"ph"});
  tree.remove(std::string{"qhk"});
  tree.remove(std::string{"rh"});
  tree.remove(std::string{"qhh"});
  tree.print();
}

void test_kv_store() {
  auto t = debug::TimeWatcher();
  auto sd = std::make_unique<driver::MemoryIO>();
  auto kv = KVStore(sd.get());
  kv.master_load();

  kv.insert(std::string{"hello"}, std::string{"world"});
  kv.insert(std::string{"i'm"}, std::string{"nghia"});
  kv.insert(std::string{"i'mm"}, std::string{"bioturi"});
  kv.insert(std::string{"nghia"}, std::string{"bioturi"});
  kv.insert(std::string{"mghia"}, std::string{"bioturi"});
  kv.insert(std::string{"hghia"}, std::string{"bioturi"});
  kv.insert(std::string{"nh"}, std::string{"bioturi"});
  kv.insert(std::string{"absldk"}, std::string{"bioturi"});
  kv.insert(std::string{"adb"}, std::string{"bioturi"});
  kv.insert(std::string{"cdb"}, std::string{"bioturi"});
  kv.insert(std::string{"ddb"}, std::string{"bioturi"});
  kv.insert(std::string{"fdb"}, std::string{"bioturi"});
  kv.insert(std::string{"ohhkhkk"}, std::string{"bioturi"});
  kv.insert(std::string{"ph"}, std::string{"bioturi"});
  kv.insert(std::string{"qhh"}, std::string{"bioturi"});
  kv.insert(std::string{"qhk"}, std::string{"bioturi"});
  kv.insert(std::string{"qhl"}, std::string{"bioturi"});
  kv.insert(std::string{"rh"}, std::string{"bioturi"});
  kv.insert(std::string{"yh"}, std::string{"bioturi"});

  kv.get_tree()->print();
  kv.get_stack()->print();

  kv.remove(std::string{"i'm"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"hello"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"mghia"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"i'mm"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"nghia"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"nh"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"hghia"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"absldk"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"adb"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"cdb"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"ohhkhkk"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"ddb"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"fdb"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"qhl"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"yh"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"ph"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"qhk"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"rh"});

  kv.get_tree()->print();
  kv.get_stack()->print();
  kv.remove(std::string{"qhh"});

  kv.get_tree()->print();
  kv.get_stack()->print();
}

int main() {
  // test_stack();
  test_btree();
  test_kv_store();
  return 0;
}