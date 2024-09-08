from database.utils import binary
from database.constants import MASTER_SIG


class MasterPage:
  # Master page structure:
  # |--------------------------------|
  # | signature | root | used | head |
  # | 16b       | 8b   | 8b   | 8b   |
  # |--------------------------------|

  def __init__(
      self,
      sig: bytes,
      root: int,
      used: int,
      head: int,
  ) -> None:
    self.sig = sig
    self.root = root
    self.used = used
    self.head = head

  def serialize(self) -> bytes:
    return (
        self.sig +
        binary.bytes8(self.root) +
        binary.bytes8(self.used) +
        binary.bytes8(self.head)
    )

  @staticmethod
  def deserialize(data: bytes) -> "MasterPage":
    master_page = MasterPage(
        data[:16],
        binary.uint64(data[16:24]),
        binary.uint64(data[24:32]),
        binary.uint64(data[32:40]),
    )
    if master_page.sig != MASTER_SIG:
      raise ValueError("Invalid signature")
    return master_page
