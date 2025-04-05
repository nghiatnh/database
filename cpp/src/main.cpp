#include <bitset>
#include <string>

#include "b_tree.h"
#include "driver/memory.h"

using namespace cpp_database;

int main() {
  auto sd = std::make_unique<driver::MemoryDriver>();
  BTree tree(std::move(sd));
  tree.insert(ByteArray{std::string{"hello"}}, ByteArray{std::string{"world"}});
  tree.print();
  tree.insert(ByteArray{std::string{"i'm"}}, ByteArray{std::string{"nghia"}});
  tree.print();
  tree.insert(ByteArray{std::string{"i'mm"}}, ByteArray{std::string{"bioturi"}});
  tree.print();
  tree.insert(ByteArray{std::string{"nghia"}}, ByteArray{std::string{"bioturi"}});
  tree.print();
  tree.insert(ByteArray{std::string{"mghia"}}, ByteArray{std::string{"bioturi"}});
  tree.print();
  tree.insert(ByteArray{std::string{"hghia"}}, ByteArray{std::string{"bioturi"}});
  tree.print();
  tree.insert(ByteArray{std::string{"nh"}}, ByteArray{std::string{"bioturi"}});
  tree.print();
  tree.insert(ByteArray{std::string{"absldk"}}, ByteArray{std::string{"bioturi"}});
  tree.insert(ByteArray{std::string{"adb"}}, ByteArray{std::string{"bioturi"}});
  tree.insert(ByteArray{std::string{"cdb"}}, ByteArray{std::string{"bioturi"}});
  tree.insert(ByteArray{std::string{"ddb"}}, ByteArray{std::string{"bioturi"}});
  tree.insert(ByteArray{std::string{"fdb"}}, ByteArray{std::string{"bioturi"}});
  tree.insert(ByteArray{std::string{"ohhkhkk"}}, ByteArray{std::string{"bioturi"}});
  tree.insert(ByteArray{std::string{"ph"}}, ByteArray{std::string{"bioturi"}});
  tree.print();
  return 0;
}