from typing import Literal

LITTLE = "little"


# Int to bytes

def bytes1(value: int, *, order: Literal["little", "big"] = LITTLE) -> bytes:
  return value.to_bytes(1, byteorder=order)


def bytes2(value: int, *, order: Literal["little", "big"] = LITTLE) -> bytes:
  return value.to_bytes(2, byteorder=order)


def bytes4(value: int, *, order: Literal["little", "big"] = LITTLE) -> bytes:
  return value.to_bytes(4, byteorder=order)


def bytes8(value: int, *, order: Literal["little", "big"] = LITTLE) -> bytes:
  return value.to_bytes(8, byteorder=order)


# Bytes to int

def int8(value: bytes, *, order: Literal["little", "big"] = LITTLE) -> int:
  return int.from_bytes(value[:1], byteorder=order)


def int16(value: bytes, *, order: Literal["little", "big"] = LITTLE) -> int:
  return int.from_bytes(value[:2], byteorder=order)


def int32(value: bytes, *, order: Literal["little", "big"] = LITTLE) -> int:
  return int.from_bytes(value[:4], byteorder=order)


def int64(value: bytes, *, order: Literal["little", "big"] = LITTLE) -> int:
  return int.from_bytes(value[:8], byteorder=order)
