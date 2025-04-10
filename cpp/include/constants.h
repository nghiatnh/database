#ifndef CPP_DATATBASE_CONSTANTS_H
#define CPP_DATATBASE_CONSTANTS_H

#include <cstddef>

namespace cpp_database {

const static int PAGE_SIZE = 256;
const static int NODE_TYPE_SZ = 1;
const static int N_KEY_SZ = 8;
const static int N_VALUE_SZ = 8;
const static int N_POINTER_SZ = 8;
const static int POINTER_SZ = 8;
const static int OFFSET_SZ = 8;
const static int KV_SIZE_SZ = 8;

const static int DB_SIGNATURE_SZ = 16;
const static char DB_SIGNATURE[DB_SIGNATURE_SZ] = "CppDatabase2025";

enum class NodeType : uint8_t {
  EMPTY,
  LEAF,
  INTERNAL,
  STACK,
};

}  // namespace cpp_database

#endif  // !CPP_DATATBASE_CONSTANTS_H