from database.utils import binary
from database.kvstore.constants import MASTER_SIG


class MasterPage:
  def __init__(
      self,
      sig: bytes,
      root: int,
      used: int,
  ) -> None:
    self.sig = sig
    self.root = root
    self.used = used

  def serialize(self) -> bytes:
    return self.sig + binary.bytes8(self.root) + binary.bytes8(self.used)

  @staticmethod
  def deserialize(data: bytes) -> "MasterPage":
    master_page = MasterPage(
        data[:16],
        binary.uint64(data[16:24]),
        binary.uint64(data[24:32]),
    )
    if master_page.sig != MASTER_SIG:
      raise ValueError("Invalid signature")
    return master_page
