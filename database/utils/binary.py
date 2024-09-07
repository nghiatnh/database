from typing import Literal


LITTLE = "little"
BIG = "big"


# =========================================================================== #
# Encoding                                                                    #
# =========================================================================== #


def bytes1(value: int, *, order: Literal["little", "big"] = LITTLE) -> bytes:
  return value.to_bytes(1, order)


def bytes2(value: int, *, order: Literal["little", "big"] = LITTLE) -> bytes:
  return value.to_bytes(2, order)


def bytes4(value: int, *, order: Literal["little", "big"] = LITTLE) -> bytes:
  return value.to_bytes(4, order)


def bytes8(value: int, *, order: Literal["little", "big"] = LITTLE) -> bytes:
  return value.to_bytes(8, order)


# =========================================================================== #
# Decoding                                                                    #
# =========================================================================== #


def uint8(value: bytes, *, order: Literal["little", "big"] = LITTLE) -> int:
  return int.from_bytes(value[:1], order)


def uint16(value: bytes, *, order: Literal["little", "big"] = LITTLE) -> int:
  return int.from_bytes(value[:2], order)


def uint32(value: bytes, *, order: Literal["little", "big"] = LITTLE) -> int:
  return int.from_bytes(value[:4], order)


def uint64(value: bytes, *, order: Literal["little", "big"] = LITTLE) -> int:
  return int.from_bytes(value[:8], order)
