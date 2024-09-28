from enum import Enum


# =========================================================================== #
# Enumerations                                                                #
# =========================================================================== #

class NodeType(Enum):
  NULL = 0
  LEAF = 1
  INTERNAL = 2
  FREE = 3


class ValueType(Enum):
  INTEGER = "INTEGER"
  TEXT = "TEXT"


class CompareOP(Enum):
  LE = -3
  LT = -2
  GT = 2
  GE = 3


class SetMode(Enum):
  INSERT_ONLY = 1
  UPDATE_ONLY = 2
  UPSERT = 3


# =========================================================================== #
# Constants                                                                   #
# =========================================================================== #


PAGE_SIZE = 4096
MAX_KEY_SZ = 1000
MAX_VALUE_SZ = 3000

QUEUE_CAP = (PAGE_SIZE - 2 - 8 - 4) // 16

MASTER_SIG = "BuildMyOwnDB2024"

TDEF_MIN_PREFIX = 3

COMPARE_FN = {
    CompareOP.LE: lambda x, y: x <= y,
    CompareOP.LT: lambda x, y: x < y,
    CompareOP.GT: lambda x, y: x > y,
    CompareOP.GE: lambda x, y: x >= y,
}
