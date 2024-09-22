from dataclasses import dataclass

from database.utils import binary


@dataclass
class MasterPage:
  """
  MasterPage
  ==========
  MasterPage class represents the master page of the KVStore.
  """

  # Master page structure:
  # | Signature | Version | Flushed | Root | Top |
  # | 16b       | 8b      | 8b      | 8b   | 8b  |

  sig: str
  version: int
  flushed: int
  root: int
  top: int

  def serialize(self) -> bytes:
    """
    Serialize the master page to bytes.
    """
    return (
        self.sig.encode() +
        binary.bytes8(self.version) +
        binary.bytes8(self.flushed) +
        binary.bytes8(self.root) +
        binary.bytes8(self.top)
    )

  @staticmethod
  def deserialize(data: bytes) -> "MasterPage":
    """
    Deserialize the master page from bytes.
    """
    return MasterPage(
        sig=data[:16].decode(),
        version=binary.int64(data[16:24]),
        flushed=binary.int64(data[24:32]),
        root=binary.int64(data[32:40]),
        top=binary.int64(data[40:48]),
    )
