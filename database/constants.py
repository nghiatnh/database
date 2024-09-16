from enum import Enum


class NodeType(Enum):
  NULL = 0
  LEAF = 1
  INTERNAL = 2
  FREE = 3


PAGE_SIZE = 4096
MAX_KEY_SZ = 1000
MAX_VALUE_SZ = 3000
