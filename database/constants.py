from enum import Enum

# =========================================================================== #
# Enumerations                                                                #
# =========================================================================== #


class NodeType(Enum):
  NULL = 0
  LEAF = 1
  INTERNAL = 2
  FREE = 3


class UpdateMode(Enum):
  INSERT_ONLY = 1
  UPDATE_ONLY = 2
  UPSERT = 3


class CompareOP(Enum):
  GE = ">="
  GT = ">"
  LT = "<"
  LE = "<="


class IndexOP(Enum):
  ADD = 1
  DELETE = 2


class ColumnType(Enum):
  ERROR = 0
  BYTES = 1
  INT = 2

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
MASTER_SIG = b"MyOwnDatabase012"

# Compare function
COMPARE_FUNC = {
    CompareOP.GE: lambda a, b: a >= b,
    CompareOP.GT: lambda a, b: a > b,
    CompareOP.LT: lambda a, b: a < b,
    CompareOP.LE: lambda a, b: a <= b,
}
