#include <bitset>
#include <string>

#include "b_tree.h"
#include "driver/memory.h"
#include "debug.h"

using namespace cpp_database;

int main() {
  auto sd = std::make_unique<driver::MemoryDriver>();
  BTree tree(std::move(sd));
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
  return 0;
}