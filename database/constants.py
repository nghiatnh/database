from enum import Enum

# =========================================================================== #
# Enumerations                                                                #
# =========================================================================== #


class NodeType(Enum):
  NULL = 0
  LEAF = 1
  INTERNAL = 2
  FREE = 3


class CompareOP(Enum):
  GE = 3
  GT = 2
  LT = -2
  LE = -3


# =========================================================================== #
# Constants                                                                   #
# =========================================================================== #


# Page
PAGE_SIZE = 4096
MAX_KEY_SIZE = 1000
MAX_VALUE_SIZE = 3000

# Free List
FREE_LIST_HEADER = 4 + 8 + 8  # type + length + next + total_length
FREE_LIST_CAP = (PAGE_SIZE - FREE_LIST_HEADER) // 8

# Master Page
MASTER_SIG = b'MyOwnDatabase012'
