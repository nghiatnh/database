#ifndef CONSTANTS_H
#define CONSTANTS_H

namespace cpp_database {

const static int PAGE_SIZE = 256;
const static int NODE_TYPE_SZ = 1;
const static int N_KEY_SZ = 8;
const static int N_VALUE_SZ = 8;
const static int N_POINTER_SZ = 8;
const static int POINTER_SZ = 8;
const static int OFFSET_SZ = 8;
const static int KV_SIZE_SZ = 8;

}  // namespace cpp_database

#endif  // !CONSTANTS_H